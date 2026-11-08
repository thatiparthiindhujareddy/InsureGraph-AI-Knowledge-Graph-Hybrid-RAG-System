"""
InsureGraph AI — RAG Chain
LangChain-based RAG pipeline with insurance-domain system prompt and source citation.
"""
import logging
import time
from typing import List, Dict, Any, Optional

from openai import OpenAI

from backend.config import settings
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.models.schemas import QueryResponse, SourceDocument, GraphContext

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are InsureGraph AI, an expert insurance policy analyst specializing in Property & Casualty (P&C) insurance.

Your role is to:
1. Answer questions about insurance policies accurately and precisely
2. Reference specific coverage limits, deductibles, exclusions, and conditions
3. Explain complex insurance concepts in clear language
4. Identify when coverage may or may not apply based on policy conditions
5. Note any multi-hop reasoning (e.g., a coverage that depends on a deductible threshold, which itself has exclusions)

CRITICAL RULES:
- Only answer based on the provided context. If information is not in the context, say so clearly.
- Always cite specific dollar amounts, percentages, or policy terms when present in the context.
- When coverage is conditional, explicitly state ALL conditions that must be met.
- Distinguish between what IS covered and what IS excluded.
- If multiple policies are present, identify which policy each answer applies to.

Format your answer clearly with:
- A direct answer first
- Supporting details and conditions
- Relevant exclusions or limitations
- Policy references (policy name, section if mentioned)
"""

QUERY_PROMPT_TEMPLATE = """Based on the following insurance policy context, answer the question accurately.

{context}

QUESTION: {question}

Provide a comprehensive answer that addresses all aspects of the question, including any conditions, exclusions, or limitations that apply."""


class InsureGraphRAGChain:
    """
    RAG chain for insurance policy Q&A.
    Integrates hybrid retrieval with LLM generation.
    """

    def __init__(self, retriever: Optional[HybridRetriever] = None):
        self.retriever = retriever or HybridRetriever()
        self.client = OpenAI(api_key=settings.openai_api_key)

    def query(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        use_graph: bool = True,
        max_hops: int = 2,
        top_k: Optional[int] = None,
    ) -> QueryResponse:
        """
        Execute a full RAG query: retrieve → prompt → generate → respond.
        """
        start_time = time.time()

        logger.info(f"RAG query: '{question[:80]}'")

        # ── 1. Hybrid Retrieval ──────────────────────────────────────────────
        retrieval = self.retriever.retrieve(
            query=question,
            use_graph=use_graph,
            max_hops=max_hops,
            top_k_vector=top_k,
            document_ids=document_ids,
        )

        # ── 2. Build Context ─────────────────────────────────────────────────
        context = self.retriever.format_context_for_llm(retrieval, max_chunks=6)

        if not context.strip():
            logger.warning("No context retrieved for query")
            context = "No relevant policy documents found in the knowledge base."

        # ── 3. LLM Generation ────────────────────────────────────────────────
        prompt = QUERY_PROMPT_TEMPLATE.format(context=context, question=question)

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1500,
        )
        answer = response.choices[0].message.content.strip()

        # ── 4. Build Source Citations ─────────────────────────────────────────
        sources = self._build_sources(retrieval.get("merged_chunks", []))

        # ── 5. Build Graph Context Response ──────────────────────────────────
        graph_ctx = self._build_graph_context_response(retrieval.get("graph_context", {}))

        # ── 6. Confidence Score ───────────────────────────────────────────────
        confidence = self._compute_confidence(retrieval, answer)

        elapsed = time.time() - start_time

        return QueryResponse(
            question=question,
            answer=answer,
            sources=sources,
            graph_context=graph_ctx,
            confidence_score=round(confidence, 3),
            processing_time_s=round(elapsed, 2),
            model_used=settings.llm_model,
        )

    def _build_sources(self, chunks: List[Dict[str, Any]]) -> List[SourceDocument]:
        """Convert retrieval chunks to SourceDocument schema."""
        sources = []
        for chunk in chunks[:6]:
            meta = chunk.get("metadata", {})
            sources.append(
                SourceDocument(
                    document_id=meta.get("document_id", "unknown"),
                    policy_name=meta.get("policy_name", "Unknown Policy"),
                    chunk_text=chunk.get("text", "")[:500] + "..."
                    if len(chunk.get("text", "")) > 500
                    else chunk.get("text", ""),
                    relevance_score=chunk.get("similarity_score", 0.0),
                    retrieval_method=chunk.get("retrieval_method", "hybrid"),
                    page_number=meta.get("page_number"),
                )
            )
        return sources

    def _build_graph_context_response(
        self, graph_ctx: Dict[str, Any]
    ) -> Optional[GraphContext]:
        """Build GraphContext schema from raw graph context dict."""
        if not graph_ctx:
            return None

        entities_found = [
            f"{n.get('entity_type', '?')}: {n.get('label', '?')}"
            for n in graph_ctx.get("context_nodes", [])[:10]
        ]

        relationships = [
            {
                "from": e.get("source_label", ""),
                "relationship": e.get("relationship", ""),
                "to": e.get("target_label", ""),
            }
            for e in graph_ctx.get("context_edges", [])[:10]
        ]

        return GraphContext(
            entities_found=entities_found,
            relationships=relationships,
            traversal_paths=graph_ctx.get("traversal_paths", [])[:5],
        )

    def _compute_confidence(
        self, retrieval: Dict[str, Any], answer: str
    ) -> float:
        """
        Heuristic confidence score based on:
        - Number and quality of retrieved chunks
        - Whether graph context was found
        - Answer length (proxy for informativeness)
        """
        vector_results = retrieval.get("vector_results", [])
        graph_context = retrieval.get("graph_context", {})

        if not vector_results:
            return 0.2

        # Average similarity of top results
        avg_similarity = sum(
            r.get("similarity_score", 0) for r in vector_results[:3]
        ) / max(len(vector_results[:3]), 1)

        # Bonus for graph context
        graph_bonus = 0.1 if graph_context.get("context_nodes") else 0.0

        # Penalty for very short answers (may indicate no context)
        length_factor = min(len(answer) / 200, 1.0) * 0.1

        score = avg_similarity * 0.8 + graph_bonus + length_factor
        return min(score, 1.0)
