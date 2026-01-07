"""
FAISS vector store management for RAG retrieval.

This module provides:
- FAISS index creation and management
- Persistent storage and loading
- Metadata tracking for filtered retrieval
- Search with metadata filtering
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """
    Metadata for a chunk stored in FAISS.
    
    Attributes:
        chunk_id: Database chunk ID.
        user_id: Owner user ID (for filtering).
        subject_id: Subject ID (for filtering).
        unit_id: Unit ID (for filtering).
        topic_id: Topic ID (for filtering).
        source_file_id: Source file ID.
    """
    
    chunk_id: int
    user_id: int
    subject_id: int
    unit_id: int
    topic_id: int
    source_file_id: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkMetadata":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SearchResult:
    """
    Result from FAISS search.
    
    Attributes:
        chunk_id: Database chunk ID.
        score: Similarity score (higher is more similar).
        metadata: Full chunk metadata.
    """
    
    chunk_id: int
    score: float
    metadata: ChunkMetadata


class FAISSVectorStore:
    """
    FAISS-based vector store with metadata filtering.
    
    Maintains a FAISS index for similarity search and a separate
    metadata store for filtering results by user/subject/unit/topic.
    """
    
    def __init__(
        self,
        index_path: str | None = None,
        metadata_path: str | None = None,
        dimension: int | None = None,
    ):
        """
        Initialize the vector store.
        
        Args:
            index_path: Path to FAISS index file. If None, uses settings.
            metadata_path: Path to metadata JSON file. If None, uses settings.
            dimension: Embedding dimension. If None, uses settings.
        """
        settings = get_settings()
        
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH)
        self.metadata_path = Path(metadata_path or settings.FAISS_METADATA_PATH)
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        
        # Initialize index and metadata
        self.index: faiss.IndexFlatIP | None = None
        self.metadata: list[ChunkMetadata] = []
        
        # Load existing index if available
        self._load_or_create()
        
        logger.info(
            f"FAISSVectorStore initialized: dimension={self.dimension}, "
            f"vectors={self.index.ntotal if self.index else 0}"
        )
    
    def _ensure_directories(self) -> None:
        """Create directories for index and metadata files."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _create_index(self) -> faiss.IndexFlatIP:
        """
        Create a new FAISS index.
        
        Uses IndexFlatIP (Inner Product) for cosine similarity.
        OpenAI embeddings are normalized, so IP = cosine similarity.
        
        Returns:
            New FAISS index.
        """
        logger.info(f"Creating new FAISS index with dimension {self.dimension}")
        return faiss.IndexFlatIP(self.dimension)
    
    def _load_or_create(self) -> None:
        """Load existing index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                self._load()
                return
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
                logger.info("Creating new index")
        
        self.index = self._create_index()
        self.metadata = []
    
    def _load(self) -> None:
        """Load index and metadata from disk."""
        logger.info(f"Loading FAISS index from {self.index_path}")
        self.index = faiss.read_index(str(self.index_path))
        
        logger.info(f"Loading metadata from {self.metadata_path}")
        with open(self.metadata_path, "r") as f:
            data = json.load(f)
            self.metadata = [ChunkMetadata.from_dict(m) for m in data]
        
        logger.info(f"Loaded {self.index.ntotal} vectors with {len(self.metadata)} metadata entries")
        
        if self.index.ntotal != len(self.metadata):
            logger.warning(
                f"Index/metadata mismatch: {self.index.ntotal} vectors, "
                f"{len(self.metadata)} metadata entries"
            )
    
    def save(self) -> None:
        """Save index and metadata to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        self._ensure_directories()
        
        logger.info(f"Saving FAISS index to {self.index_path}")
        faiss.write_index(self.index, str(self.index_path))
        
        logger.info(f"Saving metadata to {self.metadata_path}")
        with open(self.metadata_path, "w") as f:
            data = [m.to_dict() for m in self.metadata]
            json.dump(data, f)
        
        logger.info(f"Saved {self.index.ntotal} vectors")
    
    def add_embeddings(
        self,
        embeddings: list[list[float]],
        metadata_list: list[ChunkMetadata],
    ) -> list[int]:
        """
        Add embeddings to the index.
        
        Args:
            embeddings: List of embedding vectors.
            metadata_list: List of metadata for each embedding.
            
        Returns:
            List of FAISS index positions for each embedding.
            
        Raises:
            ValueError: If embeddings and metadata lengths don't match.
        """
        if len(embeddings) != len(metadata_list):
            raise ValueError(
                f"Embeddings ({len(embeddings)}) and metadata ({len(metadata_list)}) "
                "must have same length"
            )
        
        if not embeddings:
            return []
        
        if self.index is None:
            self.index = self._create_index()
        
        # Convert to numpy array
        vectors = np.array(embeddings, dtype=np.float32)
        
        # Normalize for cosine similarity (IP with normalized vectors = cosine)
        faiss.normalize_L2(vectors)
        
        # Get starting position
        start_pos = self.index.ntotal
        
        # Add to index
        self.index.add(vectors)
        
        # Add metadata
        self.metadata.extend(metadata_list)
        
        # Return positions
        positions = list(range(start_pos, start_pos + len(embeddings)))
        
        logger.info(f"Added {len(embeddings)} vectors to index (total: {self.index.ntotal})")
        
        return positions
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        user_id: int | None = None,
        subject_id: int | None = None,
        unit_id: int | None = None,
        topic_id: int | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar chunks with metadata filtering.
        
        Args:
            query_embedding: Query embedding vector.
            top_k: Number of results to return.
            user_id: Filter by user ID.
            subject_id: Filter by subject ID.
            unit_id: Filter by unit ID.
            topic_id: Filter by topic ID.
            
        Returns:
            List of SearchResult objects.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Empty index, no search results")
            return []
        
        # Convert and normalize query
        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        
        # Search with more results than needed for filtering
        # We need to over-fetch because we'll filter after
        search_k = min(top_k * 10, self.index.ntotal)
        
        logger.debug(f"Searching for {search_k} candidates (need {top_k} after filtering)")
        
        distances, indices = self.index.search(query, search_k)
        
        # Build results with filtering
        results: list[SearchResult] = []
        
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # No more results
                break
            
            meta = self.metadata[idx]
            
            # Apply filters
            if user_id is not None and meta.user_id != user_id:
                continue
            if subject_id is not None and meta.subject_id != subject_id:
                continue
            if unit_id is not None and meta.unit_id != unit_id:
                continue
            if topic_id is not None and meta.topic_id != topic_id:
                continue
            
            results.append(SearchResult(
                chunk_id=meta.chunk_id,
                score=float(distance),
                metadata=meta,
            ))
            
            if len(results) >= top_k:
                break
        
        logger.info(f"Search returned {len(results)} results after filtering")
        
        return results
    
    def get_chunk_embedding_id(self, chunk_id: int) -> int | None:
        """
        Get the FAISS index position for a chunk.
        
        Args:
            chunk_id: Database chunk ID.
            
        Returns:
            FAISS index position, or None if not found.
        """
        for i, meta in enumerate(self.metadata):
            if meta.chunk_id == chunk_id:
                return i
        return None
    
    def has_chunk(self, chunk_id: int) -> bool:
        """
        Check if a chunk is already in the index.
        
        Args:
            chunk_id: Database chunk ID.
            
        Returns:
            True if chunk is in index.
        """
        return self.get_chunk_embedding_id(chunk_id) is not None
    
    @property
    def size(self) -> int:
        """Get number of vectors in the index."""
        return self.index.ntotal if self.index else 0
    
    def clear(self) -> None:
        """Clear the index and metadata."""
        logger.info("Clearing FAISS index")
        self.index = self._create_index()
        self.metadata = []


# Singleton instance
_store: FAISSVectorStore | None = None


def get_vector_store() -> FAISSVectorStore:
    """
    Get the singleton vector store instance.
    
    Returns:
        FAISSVectorStore instance.
    """
    global _store
    if _store is None:
        _store = FAISSVectorStore()
    return _store


def reset_vector_store() -> None:
    """Reset the singleton instance (for testing)."""
    global _store
    _store = None
