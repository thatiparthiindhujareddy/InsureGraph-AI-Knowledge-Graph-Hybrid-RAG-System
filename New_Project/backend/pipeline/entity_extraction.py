"""
InsureGraph AI — LLM-Based Entity Extraction Pipeline
Uses GPT-4o-mini to extract insurance entities and relationships from policy text.
"""
import json
import logging
import re
import uuid
from typing import List, Tuple, Optional, Dict, Any

from openai import OpenAI

from backend.config import settings
from backend.models.entities import (
    InsuranceEntity,
    InsuranceRelationship,
    EntityType,
    RelationshipType,
    ENTITY_EXTRACTION_PROMPT,
    ENTITY_TYPES_LIST,
    RELATIONSHIP_TYPES_LIST,
)
from backend.pipeline.pdf_ingestion import DocumentChunk, ExtractedDocument

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """Create and return OpenAI client."""
    return OpenAI(api_key=settings.openai_api_key)


def extract_entities_from_chunk(
    chunk: DocumentChunk,
    client: Optional[OpenAI] = None,
) -> Tuple[List[InsuranceEntity], List[InsuranceRelationship]]:
    """
    Extract insurance entities and relationships from a single text chunk.
    Uses LLM with structured output prompting.
    """
    if client is None:
        client = get_openai_client()

    prompt = ENTITY_EXTRACTION_PROMPT.format(
        entity_types=", ".join(ENTITY_TYPES_LIST),
        relationship_types=", ".join(RELATIONSHIP_TYPES_LIST),
        text=chunk.text[:3000],  # Limit to avoid token overflow
    )

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert insurance document analyst. "
                        "Always respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)

        entities = []
        for e_data in data.get("entities", []):
            try:
                entity_type_str = e_data.get("entity_type", "Coverage")
                # Normalize to valid enum value
                if entity_type_str not in ENTITY_TYPES_LIST:
                    entity_type_str = "Coverage"

                entity = InsuranceEntity(
                    id=f"{chunk.document_id}_{e_data.get('id', str(uuid.uuid4())[:8])}",
                    entity_type=EntityType(entity_type_str),
                    label=e_data.get("label", "Unknown"),
                    properties=e_data.get("properties", {}),
                    source_text=e_data.get("source_text", chunk.text[:200]),
                    document_id=chunk.document_id,
                    page_number=chunk.page_number,
                    confidence=0.9,
                )
                entities.append(entity)
            except Exception as ex:
                logger.warning(f"Skipping malformed entity: {e_data} — {ex}")

        relationships = []
        for r_data in data.get("relationships", []):
            try:
                rel_type_str = r_data.get("relationship_type", "COVERS")
                if rel_type_str not in RELATIONSHIP_TYPES_LIST:
                    rel_type_str = "COVERS"

                rel = InsuranceRelationship(
                    source_id=f"{chunk.document_id}_{r_data.get('source_id', '')}",
                    target_id=f"{chunk.document_id}_{r_data.get('target_id', '')}",
                    relationship_type=RelationshipType(rel_type_str),
                    properties=r_data.get("properties", {}),
                    source_text=r_data.get("source_text", ""),
                    confidence=0.9,
                )
                relationships.append(rel)
            except Exception as ex:
                logger.warning(f"Skipping malformed relationship: {r_data} — {ex}")

        logger.debug(
            f"Chunk {chunk.chunk_id}: {len(entities)} entities, "
            f"{len(relationships)} relationships"
        )
        return entities, relationships

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for chunk {chunk.chunk_id}: {e}")
        return [], []
    except Exception as e:
        logger.error(f"Entity extraction error for chunk {chunk.chunk_id}: {e}")
        return [], []


def extract_entities_from_document(
    document: ExtractedDocument,
    max_chunks: int = 20,
    client: Optional[OpenAI] = None,
) -> Tuple[List[InsuranceEntity], List[InsuranceRelationship]]:
    """
    Extract all entities and relationships from a full document.
    Processes up to max_chunks to control API costs.
    """
    if client is None:
        client = get_openai_client()

    all_entities: List[InsuranceEntity] = []
    all_relationships: List[InsuranceRelationship] = []

    # Sample chunks evenly if document is very long
    chunks_to_process = document.chunks[:max_chunks]
    if len(document.chunks) > max_chunks:
        step = len(document.chunks) // max_chunks
        chunks_to_process = document.chunks[::step][:max_chunks]

    logger.info(
        f"Extracting entities from {len(chunks_to_process)} chunks "
        f"(total: {len(document.chunks)}) for '{document.policy_name}'"
    )

    for i, chunk in enumerate(chunks_to_process):
        logger.debug(f"Processing chunk {i+1}/{len(chunks_to_process)}")
        entities, relationships = extract_entities_from_chunk(chunk, client)
        all_entities.extend(entities)
        all_relationships.extend(relationships)

    # Deduplicate entities by label similarity
    deduplicated_entities = _deduplicate_entities(all_entities)

    # Filter relationships to only include valid entity references
    valid_entity_ids = {e.id for e in deduplicated_entities}
    valid_relationships = [
        r for r in all_relationships
        if r.source_id in valid_entity_ids and r.target_id in valid_entity_ids
    ]

    logger.info(
        f"Document '{document.policy_name}': "
        f"{len(deduplicated_entities)} entities, "
        f"{len(valid_relationships)} relationships extracted"
    )

    return deduplicated_entities, valid_relationships


def _deduplicate_entities(entities: List[InsuranceEntity]) -> List[InsuranceEntity]:
    """Remove duplicate entities by label + type combination."""
    seen: Dict[str, InsuranceEntity] = {}
    for entity in entities:
        key = f"{entity.entity_type.value}::{entity.label.lower().strip()}"
        if key not in seen:
            seen[key] = entity
        else:
            # Merge properties
            seen[key].properties.update(entity.properties)
    return list(seen.values())


def extract_entities_from_text_batch(
    texts: List[str],
    document_id: str,
    policy_name: str,
    client: Optional[OpenAI] = None,
) -> Tuple[List[InsuranceEntity], List[InsuranceRelationship]]:
    """
    Convenience function to extract from raw text list (for testing).
    """
    from backend.pipeline.pdf_ingestion import DocumentChunk
    chunks = [
        DocumentChunk(
            chunk_id=f"{document_id}_c{i}",
            document_id=document_id,
            policy_name=policy_name,
            text=text,
            page_number=1,
            chunk_index=i,
            metadata={"document_id": document_id, "policy_name": policy_name},
        )
        for i, text in enumerate(texts)
    ]

    all_entities, all_rels = [], []
    cl = client or get_openai_client()
    for chunk in chunks:
        ents, rels = extract_entities_from_chunk(chunk, cl)
        all_entities.extend(ents)
        all_rels.extend(rels)
    return all_entities, all_rels
