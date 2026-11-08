"""
InsureGraph AI — Pydantic Schemas for API request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PROPERTY = "property"
    CASUALTY = "casualty"
    AUTO = "auto"
    LIABILITY = "liability"
    COMMERCIAL = "commercial"
    HOMEOWNERS = "homeowners"
    UMBRELLA = "umbrella"


class IngestRequest(BaseModel):
    document_type: DocumentType = DocumentType.COMMERCIAL
    policy_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    success: bool
    document_id: str
    policy_name: str
    chunks_created: int
    entities_extracted: int
    graph_nodes: int
    graph_edges: int
    processing_time_s: float
    message: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, description="The insurance policy question to answer")
    document_ids: Optional[List[str]] = Field(default=None, description="Filter to specific documents")
    use_graph: bool = Field(default=True, description="Enable graph traversal for multi-hop reasoning")
    max_hops: int = Field(default=2, ge=1, le=4, description="Maximum graph traversal hops")
    top_k: Optional[int] = Field(default=None, description="Override default top-k retrieval")


class SourceDocument(BaseModel):
    document_id: str
    policy_name: str
    chunk_text: str
    relevance_score: float
    retrieval_method: str  # "vector" | "graph" | "hybrid"
    page_number: Optional[int] = None


class GraphContext(BaseModel):
    entities_found: List[str]
    relationships: List[Dict[str, str]]
    traversal_paths: List[List[str]]


class QueryResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    question: str
    answer: str
    sources: List[SourceDocument]
    graph_context: Optional[GraphContext] = None
    confidence_score: float
    processing_time_s: float
    model_used: str


class EntityNode(BaseModel):
    id: str
    label: str
    entity_type: str
    properties: Dict[str, Any]
    document_id: str
    policy_name: str


class RelationshipEdge(BaseModel):
    source: str
    target: str
    relationship_type: str
    properties: Optional[Dict[str, Any]] = None


class GraphDataResponse(BaseModel):
    nodes: List[EntityNode]
    edges: List[RelationshipEdge]
    total_nodes: int
    total_edges: int
    document_ids: List[str]


class EvaluationMetrics(BaseModel):
    faithfulness: float = Field(..., ge=0.0, le=1.0)
    answer_relevance: float = Field(..., ge=0.0, le=1.0)
    context_precision: float = Field(..., ge=0.0, le=1.0)
    context_recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)


class EvaluationResult(BaseModel):
    question_id: str
    question: str
    expected_answer: str
    generated_answer: str
    metrics: EvaluationMetrics
    judge_reasoning: str


class EvaluationReport(BaseModel):
    model_config = {"protected_namespaces": ()}
    evaluation_id: str
    timestamp: datetime
    total_questions: int
    aggregate_metrics: EvaluationMetrics
    individual_results: List[EvaluationResult]
    processing_time_s: float
    model_used: str
    judge_model: str


class DocumentInfo(BaseModel):
    document_id: str
    policy_name: str
    document_type: DocumentType
    upload_time: datetime
    chunks_count: int
    entities_count: int
    file_size_bytes: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_model: str
    vector_store: str
    graph_nodes: int
    graph_edges: int
    documents_indexed: int
