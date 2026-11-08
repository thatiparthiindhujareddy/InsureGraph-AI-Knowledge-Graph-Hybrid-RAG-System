"""
InsureGraph AI — Hybrid Retriever
Combines vector search + knowledge graph traversal for superior context retrieval.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from backend.config import settings
from backend.pipeline.vector_store import VectorStoreManager, get_vector_store
from backend.pipeline.graph_builder import InsuranceKnowledgeGraph, get_knowledge_graph

logger = logging.getLogger(__name__)


# Insurance-domain stopwords for keyword extraction
INSURANCE_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "on", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above",
    "below", "from", "up", "down", "out", "off", "over", "under", "again",
    "then", "once", "and", "but", "or", "nor", "not", "so", "yet", "both",
    "either", "neither", "this", "that", "these", "those", "what", "which",
    "who", "whom", "whose", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "than", "too", "very", "just", "any", "if", "as",
}


def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from a query for graph search."""
    # Lowercase and split
    words = re.findall(r"\b[a-z][a-z'-]{2,}\b", text.lower())
    # Remove stopwords
    keywords = [w for w in words if w not in INSURANCE_STOPWORDS]
    # Also extract key phrases (bigrams) for insurance terms
    bigrams = []
    for i in range(len(words) - 1):
        if words[i] not in INSURANCE_STOPWORDS or words[i+1] not in INSURANCE_STOPWORDS:
            bigram = f"{words[i]} {words[i+1]}"
            bigrams.append(bigram)
    return keywords + bigrams


class HybridRetriever:
    """
    Hybrid retrieval system combining:
    1. Vector search (ChromaDB) — semantic similarity
    2. Graph traversal (NetworkX) — structured relationship context
    
    Merges and re-ranks results for optimal LLM context.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStoreManager] = None,
        knowledge_graph: Optional[InsuranceKnowledgeGraph] = None,
    ):
        self.vector_store = vector_store or get_vector_store()
        self.knowledge_graph = knowledge_graph or get_knowledge_graph()

    def retrieve(
        self,
        query: str,
        use_graph: bool = True,
        max_hops: int = 2,
        top_k_vector: Optional[int] = None,
        top_k_graph: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Main retrieval method. Returns merged context from vector + graph search.
        
        Returns:
            dict with:
                - vector_results: list of chunk results from vector search
                - graph_context: structured graph neighborhood context
                - graph_context_text: formatted text representation
                - merged_chunks: deduplicated, ranked list of text chunks
                - keywords: extracted query keywords
        """
        top_k_v = top_k_vector or settings.top_k_vector
        top_k_g = top_k_graph or settings.top_k_graph

        logger.info(f"Hybrid retrieval for: '{query[:80]}...' (graph={use_graph})")

        # ── 1. Vector Search ────────────────────────────────────────────────
        vector_results = self.vector_store.search(
            query=query,
            top_k=top_k_v,
            document_ids=document_ids,
        )
        logger.debug(f"Vector search returned {len(vector_results)} results")

        # ── 2. Graph Traversal ──────────────────────────────────────────────
        graph_context = {}
        graph_context_text = ""

        if use_graph:
            keywords = extract_keywords(query)
            logger.debug(f"Graph search keywords: {keywords[:10]}")

            graph_context = self.knowledge_graph.get_graph_context_for_query(
                query_keywords=keywords,
                max_hops=max_hops,
                document_ids=document_ids,
                top_k=top_k_g,
            )
            graph_context_text = self.knowledge_graph.format_context_as_text(graph_context)
            logger.debug(
                f"Graph traversal: {len(graph_context.get('context_nodes', []))} nodes, "
                f"{len(graph_context.get('context_edges', []))} edges"
            )
        else:
            keywords = extract_keywords(query)

        # ── 3. Merge & Rank ─────────────────────────────────────────────────
        merged_chunks = self._merge_and_rank(vector_results, graph_context)

        return {
            "vector_results": vector_results,
            "graph_context": graph_context,
            "graph_context_text": graph_context_text,
            "merged_chunks": merged_chunks,
            "keywords": keywords,
        }

    def _merge_and_rank(
        self,
        vector_results: List[Dict[str, Any]],
        graph_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Merge vector search results with graph-sourced text context.
        Deduplicates and applies reciprocal rank fusion scoring.
        """
        seen_chunk_ids = set()
        merged = []

        # Add vector results (primary)
        for rank, result in enumerate(vector_results):
            chunk_id = result.get("chunk_id", "")
            if chunk_id not in seen_chunk_ids:
                result["rrf_score"] = 1.0 / (rank + 1 + 60)  # RRF formula
                result["retrieval_method"] = "vector"
                merged.append(result)
                seen_chunk_ids.add(chunk_id)

        # Supplement with source texts from graph context nodes
        for i, node in enumerate(graph_context.get("context_nodes", [])[:5]):
            source_text = node.get("source_text", "")
            if source_text and len(source_text) > 50:
                synthetic_id = f"graph_{node.get('id', i)}"
                if synthetic_id not in seen_chunk_ids:
                    merged.append({
                        "chunk_id": synthetic_id,
                        "text": source_text,
                        "metadata": {
                            "document_id": node.get("document_id", ""),
                            "policy_name": node.get("label", "Graph Context"),
                            "page_number": node.get("page_number"),
                        },
                        "similarity_score": 0.7 - (i * 0.05),
                        "rrf_score": 1.0 / (i + 1 + 60),
                        "retrieval_method": "graph",
                    })
                    seen_chunk_ids.add(synthetic_id)

        # Sort by RRF score descending
        merged.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
        return merged

    def format_context_for_llm(
        self,
        retrieval_result: Dict[str, Any],
        max_chunks: int = 6,
    ) -> str:
        """
        Build the final context string to inject into the LLM prompt.
        Combines vector chunks + graph context.
        """
        parts = []

        # Vector/hybrid chunks
        chunks = retrieval_result.get("merged_chunks", [])[:max_chunks]
        if chunks:
            parts.append("=== RETRIEVED POLICY SECTIONS ===")
            for i, chunk in enumerate(chunks, 1):
                meta = chunk.get("metadata", {})
                parts.append(
                    f"\n[Source {i} | {meta.get('policy_name', 'Policy')} "
                    f"| Page {meta.get('page_number', '?')} "
                    f"| Method: {chunk.get('retrieval_method', 'hybrid')}]"
                )
                parts.append(chunk.get("text", ""))

        # Graph context
        graph_text = retrieval_result.get("graph_context_text", "")
        if graph_text:
            parts.append(f"\n{graph_text}")

        return "\n\n".join(parts)
