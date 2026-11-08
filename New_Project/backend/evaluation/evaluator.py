"""
InsureGraph AI — LLM-as-Judge Evaluator
Implements automated evaluation metrics using an LLM judge for faithfulness,
answer relevance, context precision, and context recall.
"""
import json
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from openai import OpenAI

from backend.config import settings
from backend.models.schemas import (
    EvaluationMetrics,
    EvaluationResult,
    EvaluationReport,
)

logger = logging.getLogger(__name__)


FAITHFULNESS_PROMPT = """You are an expert evaluator assessing the faithfulness of an AI-generated answer to the provided context.

CONTEXT (Retrieved from policy documents):
{context}

GENERATED ANSWER:
{generated_answer}

Evaluate faithfulness: Does the generated answer contain ONLY information that can be supported by the context? 
Score 0.0 to 1.0 where:
- 1.0: Every claim in the answer is directly supported by the context
- 0.7: Most claims are supported, minor additions not in context
- 0.5: Half the claims are supported
- 0.0: Answer contradicts or fabricates information not in context

Return JSON: {{"score": <float>, "reasoning": "<one sentence explanation>"}}"""

ANSWER_RELEVANCE_PROMPT = """You are evaluating whether an AI answer is relevant to the given question.

QUESTION: {question}

GENERATED ANSWER: {generated_answer}

Score 0.0 to 1.0 where:
- 1.0: Answer directly and completely addresses the question
- 0.7: Answer mostly addresses the question with minor gaps
- 0.5: Partially answers the question
- 0.0: Answer is off-topic or does not address the question

Return JSON: {{"score": <float>, "reasoning": "<one sentence explanation>"}}"""

CONTEXT_PRECISION_PROMPT = """Evaluate whether the retrieved context is precise and relevant to answering the question.

QUESTION: {question}
RETRIEVED CONTEXT: {context}

Score 0.0 to 1.0 where:
- 1.0: All retrieved context is highly relevant to answering the question
- 0.7: Most context is relevant, some noise
- 0.5: About half the context is relevant
- 0.0: Context is mostly irrelevant to the question

Return JSON: {{"score": <float>, "reasoning": "<one sentence explanation>"}}"""

CONTEXT_RECALL_PROMPT = """Evaluate whether the ground truth answer could be derived from the retrieved context.

GROUND TRUTH ANSWER: {ground_truth}
RETRIEVED CONTEXT: {context}

Score 0.0 to 1.0 where:
- 1.0: The context contains all information needed to produce the ground truth answer
- 0.7: Context contains most of the needed information
- 0.5: Context contains partial information
- 0.0: Context does not contain information needed for the ground truth

Return JSON: {{"score": <float>, "reasoning": "<one sentence explanation>"}}"""


class LLMJudgeEvaluator:
    """
    Uses an LLM as judge to evaluate RAG system quality.
    Computes faithfulness, answer relevance, context precision, and context recall.
    """

    def __init__(self, judge_model: Optional[str] = None):
        self.judge_model = judge_model or settings.judge_model
        self.client = OpenAI(api_key=settings.openai_api_key)

    def _llm_judge(self, prompt: str) -> Dict[str, Any]:
        """Execute a judge prompt and parse the JSON response."""
        try:
            response = self.client.chat.completions.create(
                model=self.judge_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert RAG system evaluator. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "score": float(result.get("score", 0.0)),
                "reasoning": result.get("reasoning", ""),
            }
        except Exception as e:
            logger.error(f"LLM judge error: {e}")
            return {"score": 0.0, "reasoning": f"Evaluation error: {str(e)}"}

    def evaluate_single(
        self,
        question: str,
        generated_answer: str,
        ground_truth: str,
        context: str,
        question_id: str = "",
    ) -> EvaluationResult:
        """
        Evaluate a single Q&A pair across all metrics.
        """
        # Truncate context for judge prompt
        context_truncated = context[:3000] if context else "No context retrieved."

        # Run all four judge evaluations
        faithfulness_result = self._llm_judge(
            FAITHFULNESS_PROMPT.format(
                context=context_truncated,
                generated_answer=generated_answer,
            )
        )

        relevance_result = self._llm_judge(
            ANSWER_RELEVANCE_PROMPT.format(
                question=question,
                generated_answer=generated_answer,
            )
        )

        precision_result = self._llm_judge(
            CONTEXT_PRECISION_PROMPT.format(
                question=question,
                context=context_truncated,
            )
        )

        recall_result = self._llm_judge(
            CONTEXT_RECALL_PROMPT.format(
                ground_truth=ground_truth,
                context=context_truncated,
            )
        )

        # Compute token-based F1 as a supplementary metric
        f1, precision, recall = compute_token_f1(generated_answer, ground_truth)

        # Build reasoning summary
        reasoning = (
            f"Faithfulness: {faithfulness_result['reasoning']} | "
            f"Relevance: {relevance_result['reasoning']} | "
            f"Context Precision: {precision_result['reasoning']} | "
            f"Context Recall: {recall_result['reasoning']}"
        )

        metrics = EvaluationMetrics(
            faithfulness=round(faithfulness_result["score"], 3),
            answer_relevance=round(relevance_result["score"], 3),
            context_precision=round(precision_result["score"], 3),
            context_recall=round(recall_result["score"], 3),
            f1_score=round(f1, 3),
            precision=round(precision, 3),
            recall=round(recall, 3),
        )

        return EvaluationResult(
            question_id=question_id or str(uuid.uuid4())[:8],
            question=question,
            expected_answer=ground_truth,
            generated_answer=generated_answer,
            metrics=metrics,
            judge_reasoning=reasoning,
        )

    def evaluate_batch(
        self,
        evaluation_items: List[Dict[str, Any]],
        rag_chain=None,
    ) -> EvaluationReport:
        """
        Run evaluation across a batch of items.
        
        Each item should have: question, ground_truth, and optionally question_id.
        rag_chain should be an InsureGraphRAGChain instance.
        """
        start_time = time.time()
        results: List[EvaluationResult] = []

        logger.info(f"Starting evaluation of {len(evaluation_items)} questions...")

        for i, item in enumerate(evaluation_items):
            question = item["question"]
            ground_truth = item["ground_truth"]
            question_id = item.get("id", f"Q{i+1:03d}")

            logger.info(f"Evaluating {question_id} ({i+1}/{len(evaluation_items)}): {question[:60]}...")

            # Get RAG response
            context = ""
            generated_answer = ""

            if rag_chain:
                try:
                    query_response = rag_chain.query(question=question)
                    generated_answer = query_response.answer
                    context = "\n\n".join(
                        src.chunk_text for src in query_response.sources
                    )
                except Exception as e:
                    logger.error(f"RAG chain error for {question_id}: {e}")
                    generated_answer = f"Error generating answer: {e}"
                    context = ""
            else:
                generated_answer = item.get("generated_answer", "")
                context = item.get("context", "")

            # Evaluate
            result = self.evaluate_single(
                question=question,
                generated_answer=generated_answer,
                ground_truth=ground_truth,
                context=context,
                question_id=question_id,
            )
            results.append(result)

        # Aggregate metrics
        aggregate = _aggregate_metrics(results)
        elapsed = time.time() - start_time

        report = EvaluationReport(
            evaluation_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            total_questions=len(results),
            aggregate_metrics=aggregate,
            individual_results=results,
            processing_time_s=round(elapsed, 2),
            model_used=settings.llm_model,
            judge_model=self.judge_model,
        )

        logger.info(
            f"Evaluation complete: F1={aggregate.f1_score:.3f}, "
            f"Faithfulness={aggregate.faithfulness:.3f}, "
            f"Relevance={aggregate.answer_relevance:.3f} "
            f"({elapsed:.1f}s)"
        )

        return report


def compute_token_f1(
    predicted: str, ground_truth: str
) -> Tuple[float, float, float]:
    """
    Compute token-level F1 score between predicted and ground truth answers.
    Similar to SQuAD evaluation metric.
    """
    import re
    from collections import Counter

    def normalize(text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return text.split()

    pred_tokens = normalize(predicted)
    truth_tokens = normalize(ground_truth)

    if not pred_tokens or not truth_tokens:
        return 0.0, 0.0, 0.0

    pred_counter = Counter(pred_tokens)
    truth_counter = Counter(truth_tokens)

    common = sum((pred_counter & truth_counter).values())

    if common == 0:
        return 0.0, 0.0, 0.0

    precision = common / len(pred_tokens)
    recall = common / len(truth_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    return f1, precision, recall


def _aggregate_metrics(results: List[EvaluationResult]) -> EvaluationMetrics:
    """Compute average metrics across all evaluation results."""
    n = len(results)
    if n == 0:
        return EvaluationMetrics(
            faithfulness=0.0,
            answer_relevance=0.0,
            context_precision=0.0,
            context_recall=0.0,
            f1_score=0.0,
            precision=0.0,
            recall=0.0,
        )

    return EvaluationMetrics(
        faithfulness=round(sum(r.metrics.faithfulness for r in results) / n, 3),
        answer_relevance=round(sum(r.metrics.answer_relevance for r in results) / n, 3),
        context_precision=round(sum(r.metrics.context_precision for r in results) / n, 3),
        context_recall=round(sum(r.metrics.context_recall for r in results) / n, 3),
        f1_score=round(sum(r.metrics.f1_score for r in results) / n, 3),
        precision=round(sum(r.metrics.precision for r in results) / n, 3),
        recall=round(sum(r.metrics.recall for r in results) / n, 3),
    )
