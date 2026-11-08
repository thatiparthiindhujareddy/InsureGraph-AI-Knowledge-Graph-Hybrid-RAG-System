"""
InsureGraph AI — PDF Ingestion Pipeline
Handles PDF text extraction and intelligent chunking for insurance documents.
"""
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import fitz  # PyMuPDF

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of text extracted from a policy document."""
    chunk_id: str
    document_id: str
    policy_name: str
    text: str
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class ExtractedDocument:
    """Full extracted content from a PDF document."""
    document_id: str
    policy_name: str
    file_path: str
    file_size_bytes: int
    total_pages: int
    raw_text: str
    chunks: List[DocumentChunk]
    page_texts: Dict[int, str]
    metadata: Dict[str, Any]


def generate_document_id(file_path: str, content: str) -> str:
    """Generate a stable document ID from file path + content hash."""
    content_hash = hashlib.sha256(content[:1000].encode()).hexdigest()[:12]
    name_part = Path(file_path).stem[:20].replace(" ", "_").lower()
    return f"{name_part}_{content_hash}"


def extract_text_from_pdf(file_path: str) -> Dict[int, str]:
    """Extract text from each page of a PDF using PyMuPDF."""
    page_texts = {}
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            # Clean up whitespace artifacts
            text = "\n".join(
                line.strip() for line in text.splitlines() if line.strip()
            )
            page_texts[page_num + 1] = text
        doc.close()
        logger.info(f"Extracted {len(page_texts)} pages from {file_path}")
    except Exception as e:
        logger.error(f"Error extracting PDF {file_path}: {e}")
        raise
    return page_texts


def smart_chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[str]:
    """
    Insurance-aware text chunking that tries to preserve:
    - Coverage sections
    - Exclusion lists
    - Definition sections
    - Numbered clauses
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    # Split on insurance-specific section boundaries first
    section_markers = [
        "\nSECTION ", "\nARTICLE ", "\nPART ", "\nCOVERAGE ",
        "\nEXCLUSION", "\nCONDITION", "\nDEFINITION",
        "\n\n\n", "\n\n"
    ]

    # Try to split on meaningful boundaries
    chunks = []
    current_chunk = ""

    paragraphs = text.split("\n\n")

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph would exceed chunk size, save current chunk
        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap from end of previous
            overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + para
        else:
            current_chunk += ("\n\n" if current_chunk else "") + para

    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Handle paragraphs that are still too long
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= chunk_size * 1.5:
            final_chunks.append(chunk)
        else:
            # Hard split long chunks
            for i in range(0, len(chunk), chunk_size - chunk_overlap):
                sub_chunk = chunk[i:i + chunk_size]
                if sub_chunk.strip():
                    final_chunks.append(sub_chunk.strip())

    return final_chunks


def ingest_pdf(
    file_path: str,
    policy_name: Optional[str] = None,
    document_type: str = "commercial",
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> ExtractedDocument:
    """
    Main ingestion function: PDF → ExtractedDocument with chunks.
    """
    file_path = str(file_path)
    file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0

    if not policy_name:
        policy_name = Path(file_path).stem.replace("_", " ").title()

    logger.info(f"Ingesting PDF: {file_path} [{policy_name}]")

    # Extract text per page
    page_texts = extract_text_from_pdf(file_path)
    total_pages = len(page_texts)
    raw_text = "\n\n".join(page_texts.values())

    # Generate document ID
    document_id = generate_document_id(file_path, raw_text)

    # Create chunks with page tracking
    chunks: List[DocumentChunk] = []
    chunk_idx = 0

    for page_num, page_text in page_texts.items():
        if not page_text.strip():
            continue
        page_chunks = smart_chunk_text(page_text)
        for chunk_text in page_chunks:
            if len(chunk_text) < 50:  # skip tiny chunks
                continue
            chunk_id = f"{document_id}_p{page_num}_c{chunk_idx}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                policy_name=policy_name,
                text=chunk_text,
                page_number=page_num,
                chunk_index=chunk_idx,
                metadata={
                    "document_id": document_id,
                    "policy_name": policy_name,
                    "document_type": document_type,
                    "page_number": page_num,
                    "chunk_index": chunk_idx,
                    **(extra_metadata or {}),
                },
            )
            chunks.append(chunk)
            chunk_idx += 1

    logger.info(
        f"Document '{policy_name}' [{document_id}]: "
        f"{total_pages} pages → {len(chunks)} chunks"
    )

    return ExtractedDocument(
        document_id=document_id,
        policy_name=policy_name,
        file_path=file_path,
        file_size_bytes=file_size,
        total_pages=total_pages,
        raw_text=raw_text,
        chunks=chunks,
        page_texts=page_texts,
        metadata={
            "document_type": document_type,
            "total_chunks": len(chunks),
            **(extra_metadata or {}),
        },
    )


def ingest_text(
    text: str,
    policy_name: str,
    document_type: str = "commercial",
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> ExtractedDocument:
    """
    Ingest raw text directly (useful for testing or non-PDF sources).
    """
    document_id = generate_document_id(policy_name, text)
    raw_chunks = smart_chunk_text(text)
    chunks = []
    for idx, chunk_text in enumerate(raw_chunks):
        if len(chunk_text) < 50:
            continue
        chunk = DocumentChunk(
            chunk_id=f"{document_id}_c{idx}",
            document_id=document_id,
            policy_name=policy_name,
            text=chunk_text,
            page_number=1,
            chunk_index=idx,
            metadata={
                "document_id": document_id,
                "policy_name": policy_name,
                "document_type": document_type,
                **(extra_metadata or {}),
            },
        )
        chunks.append(chunk)

    return ExtractedDocument(
        document_id=document_id,
        policy_name=policy_name,
        file_path="",
        file_size_bytes=len(text.encode()),
        total_pages=1,
        raw_text=text,
        chunks=chunks,
        page_texts={1: text},
        metadata={"document_type": document_type, **(extra_metadata or {})},
    )
