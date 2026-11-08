"""
InsureGraph AI — Query Router
POST /api/query  — Ask questions about ingested policy documents
"""
import logging

from fastapi import APIRouter, HTTPException

from backend.models.schemas import QueryRequest, QueryResponse
from backend.rag.chain import InsureGraphRAGChain

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["Query"])

# Lazy initialization
_rag_chain: InsureGraphRAGChain = None


def get_rag_chain() -> InsureGraphRAGChain:
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = InsureGraphRAGChain()
    return _rag_chain


@router.post("", response_model=QueryResponse)
async def query_policies(request: QueryRequest):
    """
    Query the insurance policy knowledge base using hybrid retrieval (vector + graph).
    Returns a detailed answer with source citations and graph context.
    """
    try:
        chain = get_rag_chain()
        result = chain.query(
            question=request.question,
            document_ids=request.document_ids,
            use_graph=request.use_graph,
            max_hops=request.max_hops,
            top_k=request.top_k,
        )
        return result
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
