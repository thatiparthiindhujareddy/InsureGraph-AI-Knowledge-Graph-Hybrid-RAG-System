"""
InsureGraph AI — ChromaDB Vector Store Manager
Manages document embeddings for semantic similarity search.
"""
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from backend.config import settings
from backend.pipeline.pdf_ingestion import DocumentChunk, ExtractedDocument

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manages ChromaDB vector store for insurance document chunks.
    Provides embedding, storage, and semantic search capabilities.
    """

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None
        self._openai_client: Optional[OpenAI] = None
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        try:
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
            logger.info(
                f"ChromaDB initialized: collection '{settings.chroma_collection_name}' "
                f"with {self._collection.count()} documents"
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI."""
        # Truncate texts to avoid token limits
        truncated = [t[:8000] for t in texts]

        response = self._openai_client.embeddings.create(
            model=settings.embedding_model,
            input=truncated,
        )
        return [item.embedding for item in response.data]

    def add_chunks(self, chunks: List[DocumentChunk], batch_size: int = 50) -> int:
        """
        Add document chunks to the vector store.
        Returns number of chunks successfully added.
        """
        added = 0
        # Filter out chunks already in the store
        existing_ids = set()
        try:
            result = self._collection.get(ids=[c.chunk_id for c in chunks])
            existing_ids = set(result["ids"])
        except Exception:
            pass

        new_chunks = [c for c in chunks if c.chunk_id not in existing_ids]

        if not new_chunks:
            logger.info("All chunks already in vector store, skipping.")
            return 0

        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]
            try:
                texts = [c.text for c in batch]
                embeddings = self._embed_texts(texts)

                self._collection.add(
                    ids=[c.chunk_id for c in batch],
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=[c.metadata for c in batch],
                )
                added += len(batch)
                logger.debug(f"Added batch {i//batch_size + 1}: {len(batch)} chunks")
            except Exception as e:
                logger.error(f"Error adding batch {i//batch_size + 1}: {e}")

        logger.info(f"Vector store: added {added} new chunks")
        return added

    def add_document(self, document: ExtractedDocument) -> int:
        """Add all chunks from an extracted document."""
        return self.add_chunks(document.chunks)

    def search(
        self,
        query: str,
        top_k: int = None,
        document_ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant chunks.
        Returns list of result dicts with text, metadata, and distance score.
        """
        top_k = top_k or settings.top_k_vector

        # Build filter
        where_filter = {}
        if document_ids:
            if len(document_ids) == 1:
                where_filter["document_id"] = {"$eq": document_ids[0]}
            else:
                where_filter["document_id"] = {"$in": document_ids}
        if where:
            where_filter.update(where)

        try:
            # Embed the query
            query_embedding = self._embed_texts([query])[0]

            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": min(top_k, self._collection.count() or 1),
                "include": ["documents", "metadatas", "distances"],
            }
            if where_filter:
                query_kwargs["where"] = where_filter

            results = self._collection.query(**query_kwargs)

            output = []
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]
                # Convert cosine distance to similarity score (0-1)
                similarity = 1.0 - distance
                output.append({
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": round(similarity, 4),
                    "retrieval_method": "vector",
                })
            return output

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks for a specific document."""
        try:
            result = self._collection.get(
                where={"document_id": {"$eq": document_id}},
                include=["documents", "metadatas"],
            )
            return [
                {"chunk_id": id_, "text": doc, "metadata": meta}
                for id_, doc, meta in zip(
                    result["ids"], result["documents"], result["metadatas"]
                )
            ]
        except Exception as e:
            logger.error(f"Error fetching chunks for document {document_id}: {e}")
            return []

    def delete_document(self, document_id: str) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        try:
            chunks = self.get_document_chunks(document_id)
            if chunks:
                chunk_ids = [c["chunk_id"] for c in chunks]
                self._collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
                return len(chunk_ids)
            return 0
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Return vector store statistics."""
        try:
            count = self._collection.count()
            return {
                "total_chunks": count,
                "collection_name": settings.chroma_collection_name,
                "embedding_model": settings.embedding_model,
            }
        except Exception as e:
            return {"error": str(e)}

    def collection_count(self) -> int:
        """Return number of chunks in the collection."""
        try:
            return self._collection.count()
        except Exception:
            return 0


# Global singleton
_vector_store_instance: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    """Get or create the singleton vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreManager()
    return _vector_store_instance
