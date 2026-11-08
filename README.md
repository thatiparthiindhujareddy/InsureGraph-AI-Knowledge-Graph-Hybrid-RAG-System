# InsureGraph AI 🛡️

**An Intelligent Property & Casualty (P&C) Policy RAG & Knowledge Graph System**

InsureGraph AI ingests complex P&C insurance policy documents, extracts entities and relationships into a knowledge graph, enables hybrid retrieval (vector search + graph traversal), and includes an automated evaluation pipeline to score system accuracy.

---

## 🏗️ Architecture

```
insuregraph-ai/
├── backend/
│   ├── main.py                    # FastAPI app entrypoint
│   ├── config.py                  # Settings & env vars
│   ├── models/
│   │   ├── schemas.py             # Pydantic API models
│   │   └── entities.py            # Insurance entity taxonomy
│   ├── pipeline/
│   │   ├── pdf_ingestion.py       # PDF text extraction + chunking
│   │   ├── entity_extraction.py   # LLM-based NER (GPT-4o-mini)
│   │   ├── graph_builder.py       # NetworkX knowledge graph
│   │   └── vector_store.py        # ChromaDB embeddings
│   ├── retrieval/
│   │   └── hybrid_retriever.py    # Vector + Graph hybrid search (RRF)
│   ├── rag/
│   │   └── chain.py               # LangChain RAG pipeline
│   ├── evaluation/
│   │   ├── golden_dataset.py      # 25 golden Q&A pairs
│   │   └── evaluator.py           # LLM-as-judge metrics
│   └── routers/
│       ├── ingest.py              # POST /api/ingest
│       ├── query.py               # POST /api/query
│       ├── graph.py               # GET /api/graph
│       └── evaluate.py            # POST /api/evaluate
├── frontend/
│   ├── index.html                 # SPA with sidebar nav
│   ├── styles.css                 # Premium dark-mode design
│   └── app.js                     # D3.js graph + chat UI
├── data/                          # Auto-created at runtime
├── requirements.txt
├── run.py                         # Quick start script
└── .env.example
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd c:\New_Project
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

```env
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
JUDGE_MODEL=gpt-4o
```

### 3. Run the Server

```bash
python run.py
```

Open: **http://localhost:8000**

API Docs: **http://localhost:8000/api/docs**

---

## 📦 Core Modules

### 1. Knowledge Graph & Entity Extraction Pipeline

Extracts insurance entities using GPT-4o-mini with structured JSON output:

| Entity Type | Description |
|-------------|-------------|
| `Policy` | The policy document itself |
| `Policyholder` | Named insured party |
| `Coverage` | Coverage section (Building, BPP, Liability) |
| `CoverageLimit` | Dollar limits per occurrence/aggregate |
| `Deductible` | Per-occurrence, aggregate, or percentage deductibles |
| `Exclusion` | What is explicitly NOT covered |
| `Peril` | Named hazards (fire, flood, earthquake) |
| `Premium` | Policy cost and payment terms |
| `Endorsement` | Policy modifications/extensions |
| `Condition` | Policy conditions and obligations |

Relationships model multi-hop questions:
- `HOLDS_POLICY` → `HAS_DEDUCTIBLE` → `APPLIES_TO` → Peril
- `COVERAGE` → `EXCLUDES` → `Exclusion`
- `POLICY` → `COVERS` → `InsuredProperty` → `HAS_LIMIT`

### 2. RAG & Hybrid Search Engine

- **Vector Search**: ChromaDB + OpenAI `text-embedding-3-small` for semantic similarity
- **Graph Traversal**: NetworkX multi-hop traversal from matched seed entities
- **Hybrid Ranking**: Reciprocal Rank Fusion (RRF) merges results
- **Context Assembly**: Combined vector chunks + graph context text fed to LLM

### 3. Evaluation Harness

25 golden Q&A pairs covering:
- Coverage determination (easy-hard)
- Exclusion analysis
- Deductible calculations
- Multi-hop reasoning (e.g., fire → property + BI claim → deductible → total payout)
- Liability questions
- Business interruption scenarios

**Metrics (LLM-as-Judge)**:
| Metric | Description |
|--------|-------------|
| **Faithfulness** | Does the answer only use info from context? |
| **Answer Relevance** | Does the answer address the question? |
| **Context Precision** | Is the retrieved context relevant? |
| **Context Recall** | Does context contain enough to answer? |
| **Token F1** | Token-level overlap with ground truth |

---

## 🔌 API Reference

### Ingest

```bash
# Upload PDF
curl -X POST http://localhost:8000/api/ingest/upload \
  -F "file=@policy.pdf" \
  -F "document_type=commercial" \
  -F "policy_name=My Policy 2024"

# Ingest text directly
curl -X POST http://localhost:8000/api/ingest/text \
  -F "text=POLICY TEXT HERE" \
  -F "policy_name=Test Policy" \
  -F "document_type=commercial"
```

### Query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is covered if a fire destroys the building and we lose income for 3 months?",
    "use_graph": true,
    "max_hops": 2
  }'
```

### Knowledge Graph

```bash
# Get full graph data
curl http://localhost:8000/api/graph

# Search entities
curl "http://localhost:8000/api/graph/search?q=flood+deductible"

# Get node neighborhood
curl "http://localhost:8000/api/graph/neighborhood/{node_id}?max_hops=2"
```

### Evaluation

```bash
# Run evaluation on 10 questions
curl -X POST "http://localhost:8000/api/evaluate/run?max_questions=10"

# View golden dataset
curl http://localhost:8000/api/evaluate/dataset
```

---

## 🎨 Frontend Features

| Section | Features |
|---------|----------|
| **Ingest** | PDF drag-and-drop upload, sample policy loader, progress steps |
| **Query** | Chat interface with hybrid toggle, source citations, graph context panel |
| **Knowledge Graph** | D3.js force-directed visualization, entity filtering, node detail panel |
| **Evaluation** | Metric cards, radar chart, per-question results table, dataset browser |
| **Documents** | Document list with stats and delete functionality |

---

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Backend | FastAPI + Uvicorn |
| LLM | OpenAI GPT-4o-mini (extraction) / GPT-4o (judge) |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | ChromaDB (persistent) |
| Knowledge Graph | NetworkX (pickled persistence) |
| PDF Processing | PyMuPDF (fitz) |
| Frontend | Vanilla HTML/CSS/JS + D3.js |

---

## 📊 Sample Evaluation Output

```json
{
  "aggregate_metrics": {
    "faithfulness": 0.872,
    "answer_relevance": 0.891,
    "context_precision": 0.834,
    "context_recall": 0.789,
    "f1_score": 0.743,
    "precision": 0.761,
    "recall": 0.726
  },
  "total_questions": 10,
  "processing_time_s": 127.4
}
```

---

## 📝 License

MIT License — InsureGraph AI 2024
