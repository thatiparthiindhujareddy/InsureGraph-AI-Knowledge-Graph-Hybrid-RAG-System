"""
InsureGraph AI — Evaluation Router
POST /api/evaluate/run  — Run the full evaluation harness
POST /api/evaluate/single — Evaluate a single question
GET  /api/evaluate/dataset — View the golden dataset
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from backend.evaluation.golden_dataset import GOLDEN_DATASET, get_dataset_by_category
from backend.evaluation.evaluator import LLMJudgeEvaluator
from backend.models.schemas import EvaluationReport
from backend.rag.chain import InsureGraphRAGChain

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluate", tags=["Evaluation"])

_last_report: Optional[EvaluationReport] = None
_evaluation_running: bool = False


@router.get("/dataset")
async def get_golden_dataset(
    category: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
):
    """View the golden evaluation dataset."""
    data = GOLDEN_DATASET
    if category:
        data = [q for q in data if q.get("category") == category]
    if difficulty:
        data = [q for q in data if q.get("difficulty") == difficulty]
    return {
        "total": len(data),
        "questions": data,
        "categories": list({q["category"] for q in GOLDEN_DATASET}),
        "difficulties": list({q["difficulty"] for q in GOLDEN_DATASET}),
    }


@router.post("/run", response_model=EvaluationReport)
async def run_evaluation(
    max_questions: int = Query(default=10, ge=1, le=25, description="Number of questions to evaluate (max 25)"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
):
    """
    Run the full evaluation harness:
    1. For each golden dataset question, generate an answer using the RAG system
    2. Score using LLM-as-judge (faithfulness, relevance, precision, recall)
    3. Compute aggregate F1, precision, recall
    Returns a full EvaluationReport.
    """
    global _evaluation_running, _last_report

    if _evaluation_running:
        raise HTTPException(
            status_code=429,
            detail="Evaluation is already running. Please wait for it to complete.",
        )

    _evaluation_running = True

    try:
        # Select questions
        dataset = GOLDEN_DATASET
        if category:
            dataset = [q for q in dataset if q.get("category") == category]
        dataset = dataset[:max_questions]

        if not dataset:
            raise HTTPException(status_code=404, detail="No questions found for the given filters.")

        rag_chain = InsureGraphRAGChain()
        evaluator = LLMJudgeEvaluator()

        report = evaluator.evaluate_batch(
            evaluation_items=dataset,
            rag_chain=rag_chain,
        )

        _last_report = report
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    finally:
        _evaluation_running = False


@router.get("/last-report")
async def get_last_evaluation_report():
    """Return the most recent evaluation report."""
    if _last_report is None:
        raise HTTPException(status_code=404, detail="No evaluation has been run yet.")
    return _last_report


@router.post("/single")
async def evaluate_single_question(
    question: str,
    generated_answer: str,
    ground_truth: str,
    context: str = "",
):
    """Evaluate a single Q&A pair using the LLM judge."""
    try:
        evaluator = LLMJudgeEvaluator()
        result = evaluator.evaluate_single(
            question=question,
            generated_answer=generated_answer,
            ground_truth=ground_truth,
            context=context,
        )
        return result
    except Exception as e:
        logger.error(f"Single evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
