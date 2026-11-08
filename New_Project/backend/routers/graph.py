"""
InsureGraph AI — Knowledge Graph Router
GET /api/graph        — Get full graph data for visualization
GET /api/graph/stats  — Graph statistics
GET /api/graph/search — Search entities
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException

from backend.pipeline.graph_builder import get_knowledge_graph
from backend.models.schemas import GraphDataResponse, EntityNode, RelationshipEdge

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])


@router.get("", response_model=GraphDataResponse)
async def get_graph_data(
    document_id: Optional[str] = Query(default=None, description="Filter by document ID"),
    max_nodes: int = Query(default=200, ge=1, le=1000, description="Max nodes to return"),
):
    """
    Return the full knowledge graph data for frontend visualization.
    Supports filtering by document ID.
    """
    kg = get_knowledge_graph()
    all_nodes = kg.get_all_nodes_for_api()
    all_edges = kg.get_all_edges_for_api()

    # Filter by document if specified
    if document_id:
        filtered_node_ids = {
            n["id"] for n in all_nodes
            if n.get("document_id") == document_id
        }
        all_nodes = [n for n in all_nodes if n["id"] in filtered_node_ids]
        all_edges = [
            e for e in all_edges
            if e["source"] in filtered_node_ids and e["target"] in filtered_node_ids
        ]

    # Limit for performance
    all_nodes = all_nodes[:max_nodes]
    node_ids = {n["id"] for n in all_nodes}
    all_edges = [e for e in all_edges if e["source"] in node_ids and e["target"] in node_ids]

    # Convert to schema
    nodes = [
        EntityNode(
            id=n["id"],
            label=n.get("label", n["id"]),
            entity_type=n.get("entity_type", "Unknown"),
            properties=n.get("properties", {}),
            document_id=n.get("document_id", ""),
            policy_name=n.get("label", ""),
        )
        for n in all_nodes
    ]

    edges = [
        RelationshipEdge(
            source=e["source"],
            target=e["target"],
            relationship_type=e.get("relationship_type", "RELATED_TO"),
            properties=e.get("properties", {}),
        )
        for e in all_edges
    ]

    stats = kg.get_stats()

    return GraphDataResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=stats["total_nodes"],
        total_edges=stats["total_edges"],
        document_ids=stats["documents"],
    )


@router.get("/stats")
async def get_graph_stats():
    """Return knowledge graph statistics."""
    kg = get_knowledge_graph()
    return kg.get_stats()


@router.get("/search")
async def search_entities(
    q: str = Query(..., description="Search query terms"),
    entity_types: Optional[str] = Query(default=None, description="Comma-separated entity types"),
    document_id: Optional[str] = Query(default=None),
    top_k: int = Query(default=20, ge=1, le=100),
):
    """Search entities in the knowledge graph."""
    kg = get_knowledge_graph()
    keywords = q.split()
    types = entity_types.split(",") if entity_types else None
    doc_ids = [document_id] if document_id else None

    results = kg.search_entities(
        query_terms=keywords,
        entity_types=types,
        document_ids=doc_ids,
        top_k=top_k,
    )
    return {"results": results, "count": len(results)}


@router.get("/neighborhood/{node_id}")
async def get_node_neighborhood(
    node_id: str,
    max_hops: int = Query(default=2, ge=1, le=4),
):
    """Get the neighborhood (connected entities) of a specific graph node."""
    kg = get_knowledge_graph()
    if not kg.graph.has_node(node_id):
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found in graph.")
    neighborhood = kg.get_neighbors(node_id, max_hops=max_hops)
    return neighborhood
