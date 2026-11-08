"""
InsureGraph AI — Ingest Router
POST /api/ingest/upload  — Upload and process a PDF policy document
POST /api/ingest/text    — Ingest raw text directly
GET  /api/ingest/documents — List all ingested documents
DELETE /api/ingest/documents/{doc_id} — Remove a document
"""
import logging
import time
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.models.schemas import (
    IngestResponse,
    DocumentListResponse,
    DocumentInfo,
    DocumentType,
)
from backend.pipeline.pdf_ingestion import ingest_pdf, ingest_text
from backend.pipeline.entity_extraction import extract_entities_from_document
from backend.pipeline.graph_builder import get_knowledge_graph
from backend.pipeline.vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

# In-memory document registry (persisted to JSON for simplicity)
DOCUMENTS_REGISTRY_PATH = "./data/documents_registry.json"


def _load_registry() -> dict:
    path = Path(DOCUMENTS_REGISTRY_PATH)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_registry(registry: dict):
    Path(DOCUMENTS_REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(DOCUMENTS_REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2, default=str)


@router.post("/upload", response_model=IngestResponse)
async def upload_and_ingest(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(default=DocumentType.COMMERCIAL),
    policy_name: Optional[str] = Form(default=None),
):
    """
    Upload a PDF policy document and trigger the ingestion pipeline:
    1. PDF text extraction
    2. Intelligent chunking
    3. Vector embedding (ChromaDB)
    4. Entity extraction (LLM)
    5. Knowledge graph construction (NetworkX)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    start_time = time.time()

    # Save upload to disk
    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Uploaded file: {file_path} ({len(content)} bytes)")

    try:
        # ── 1. PDF Ingestion ───────────────────────────────────────────────
        document = ingest_pdf(
            file_path=str(file_path),
            policy_name=policy_name or Path(file.filename).stem.replace("_", " ").title(),
            document_type=document_type.value,
        )

        # ── 2. Vector Store ────────────────────────────────────────────────
        vector_store = get_vector_store()
        vector_store.add_document(document)

        # ── 3. Entity Extraction & Graph Building ──────────────────────────
        knowledge_graph = get_knowledge_graph()
        entities, relationships = extract_entities_from_document(document)
        nodes_added, edges_added = knowledge_graph.build_from_extraction(
            entities, relationships
        )

        elapsed = time.time() - start_time

        # ── 4. Register document ───────────────────────────────────────────
        registry = _load_registry()
        registry[document.document_id] = {
            "document_id": document.document_id,
            "policy_name": document.policy_name,
            "document_type": document_type.value,
            "upload_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "chunks_count": len(document.chunks),
            "entities_count": len(entities),
            "file_size_bytes": document.file_size_bytes,
            "file_path": str(file_path),
        }
        _save_registry(registry)

        return IngestResponse(
            success=True,
            document_id=document.document_id,
            policy_name=document.policy_name,
            chunks_created=len(document.chunks),
            entities_extracted=len(entities),
            graph_nodes=nodes_added,
            graph_edges=edges_added,
            processing_time_s=round(elapsed, 2),
            message=f"Successfully ingested '{document.policy_name}' with {len(document.chunks)} chunks and {len(entities)} entities.",
        )

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/text", response_model=IngestResponse)
async def ingest_text_document(
    text: str = Form(...),
    policy_name: str = Form(...),
    document_type: DocumentType = Form(default=DocumentType.COMMERCIAL),
):
    """Ingest raw policy text directly (no PDF upload required)."""
    start_time = time.time()

    try:
        document = ingest_text(
            text=text,
            policy_name=policy_name,
            document_type=document_type.value,
        )

        vector_store = get_vector_store()
        vector_store.add_document(document)

        knowledge_graph = get_knowledge_graph()
        entities, relationships = extract_entities_from_document(document)
        nodes_added, edges_added = knowledge_graph.build_from_extraction(entities, relationships)

        elapsed = time.time() - start_time

        registry = _load_registry()
        registry[document.document_id] = {
            "document_id": document.document_id,
            "policy_name": document.policy_name,
            "document_type": document_type.value,
            "upload_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "chunks_count": len(document.chunks),
            "entities_count": len(entities),
            "file_size_bytes": document.file_size_bytes,
        }
        _save_registry(registry)

        return IngestResponse(
            success=True,
            document_id=document.document_id,
            policy_name=document.policy_name,
            chunks_created=len(document.chunks),
            entities_extracted=len(entities),
            graph_nodes=nodes_added,
            graph_edges=edges_added,
            processing_time_s=round(elapsed, 2),
            message=f"Text document '{policy_name}' ingested successfully.",
        )

    except Exception as e:
        logger.error(f"Text ingestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """Return a list of all ingested documents."""
    from datetime import datetime
    registry = _load_registry()
    docs = []
    for doc_id, info in registry.items():
        try:
            docs.append(
                DocumentInfo(
                    document_id=info["document_id"],
                    policy_name=info["policy_name"],
                    document_type=DocumentType(info.get("document_type", "commercial")),
                    upload_time=datetime.fromisoformat(
                        info["upload_time"].replace("Z", "+00:00")
                    ),
                    chunks_count=info.get("chunks_count", 0),
                    entities_count=info.get("entities_count", 0),
                    file_size_bytes=info.get("file_size_bytes", 0),
                )
            )
        except Exception as e:
            logger.warning(f"Skipping malformed registry entry {doc_id}: {e}")
    return DocumentListResponse(documents=docs, total_count=len(docs))


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Remove a document from the vector store and knowledge graph."""
    registry = _load_registry()
    if document_id not in registry:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    vector_store = get_vector_store()
    knowledge_graph = get_knowledge_graph()

    chunks_deleted = vector_store.delete_document(document_id)
    nodes_deleted = knowledge_graph.remove_document(document_id)

    del registry[document_id]
    _save_registry(registry)

    return {
        "success": True,
        "document_id": document_id,
        "chunks_deleted": chunks_deleted,
        "nodes_deleted": nodes_deleted,
    }
