"""
InsureGraph AI — Application Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")

    llm_model: str = Field(default="gpt-4o-mini", env="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    judge_model: str = Field(default="gpt-4o", env="JUDGE_MODEL")

    # Vector Store
    chroma_persist_dir: str = Field(default="./data/chroma_db", env="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(default="insurance_policies", env="CHROMA_COLLECTION_NAME")

    # Knowledge Graph
    graph_persist_path: str = Field(default="./data/knowledge_graph.pkl", env="GRAPH_PERSIST_PATH")

    # App
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    debug: bool = Field(default=True, env="DEBUG")

    # Chunking
    chunk_size: int = Field(default=800, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, env="CHUNK_OVERLAP")
    top_k_vector: int = Field(default=5, env="TOP_K_VECTOR")
    top_k_graph: int = Field(default=3, env="TOP_K_GRAPH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure data directories exist
Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
Path(settings.graph_persist_path).parent.mkdir(parents=True, exist_ok=True)
Path("./data/sample_policies").mkdir(parents=True, exist_ok=True)
Path("./data/uploads").mkdir(parents=True, exist_ok=True)
