"""
InsureGraph AI — FastAPI Main Application
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.routers import ingest, query, graph, evaluate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("=" * 60)
    logger.info("InsureGraph AI — Starting Up")
    logger.info(f"LLM Model: {settings.llm_model}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info(f"Judge Model: {settings.judge_model}")
    logger.info(f"ChromaDB: {settings.chroma_persist_dir}")
    logger.info(f"Graph: {settings.graph_persist_path}")
    logger.info("=" * 60)

    # Pre-warm singleton instances
    from backend.pipeline.vector_store import get_vector_store
    from backend.pipeline.graph_builder import get_knowledge_graph

    vs = get_vector_store()
    kg = get_knowledge_graph()
    stats = kg.get_stats()
    vs_stats = vs.get_stats()

    logger.info(
        f"Vector Store: {vs_stats.get('total_chunks', 0)} chunks | "
        f"Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges"
    )

    yield

    logger.info("InsureGraph AI — Shutting Down")


app = FastAPI(
    title="InsureGraph AI",
    description=(
        "An Intelligent P&C Insurance Policy RAG & Knowledge Graph System. "
        "Ingest policy documents, extract entities, query with hybrid retrieval, "
        "and evaluate system accuracy with the built-in LLM judge harness."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(graph.router)
app.include_router(evaluate.router)


@app.get("/api/health")
async def health_check():
    """System health check endpoint."""
    from backend.pipeline.vector_store import get_vector_store
    from backend.pipeline.graph_builder import get_knowledge_graph
    from backend.routers.ingest import _load_registry

    kg = get_knowledge_graph()
    vs = get_vector_store()
    registry = _load_registry()
    stats = kg.get_stats()

    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "judge_model": settings.judge_model,
        "vector_store": f"{vs.collection_count()} chunks",
        "graph_nodes": stats["total_nodes"],
        "graph_edges": stats["total_edges"],
        "documents_indexed": len(registry),
    }


# Serve frontend static files
frontend_dir = Path("./frontend")
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory="./frontend"), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse("./frontend/index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse("./frontend/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="info",
    )
