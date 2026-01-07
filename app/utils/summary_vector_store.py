"""
Separate FAISS vector store for summary embeddings.

This module provides a FAISS index specifically for summaries,
separate from the chunk index, with appropriate metadata for
topic and unit summaries.
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Literal

import faiss
import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SummaryMetadata:
    """
    Metadata for a summary stored in FAISS.
    
    Attributes:
        summary_id: Database summary ID.
        summary_type: Either "topic" or "unit".
        user_id: Owner user ID (for filtering).
        subject_id: Subject ID (for filtering).
        unit_id: Unit ID (for filtering).
        topic_id: Topic ID (only for topic summaries).
    """
    
    summary_id: int
    summary_type: Literal["topic", "unit"]
    user_id: int
    subject_id: int
    unit_id: int
    topic_id: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SummaryMetadata":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SummarySearchResult:
    """
    Result from FAISS summary search.
    
    Attributes:
        summary_id: Database summary ID.
        summary_type: Either "topic" or "unit".
        score: Similarity score (higher is more similar).
        metadata: Full summary metadata.
    """
    
    summary_id: int
    summary_type: Literal["topic", "unit"]
    score: float
    metadata: SummaryMetadata


class SummaryVectorStore:
    """
    FAISS-based vector store for summary embeddings.
    
    Separate from the chunk index to allow different retrieval
    strategies for summaries vs raw chunks.
    """
    
    def __init__(
        self,
        index_path: str | None = None,
        metadata_path: str | None = None,
        dimension: int | None = None,
    ):
        """
        Initialize the summary vector store.
        
        Args:
            index_path: Path to FAISS index file.
            metadata_path: Path to metadata JSON file.
            dimension: Embedding dimension.
        """
        settings = get_settings()
        
        # Use separate paths for summary index
        default_index = settings.FAISS_INDEX_PATH.replace("index.faiss", "summary_index.faiss")
        default_metadata = settings.FAISS_METADATA_PATH.replace("metadata.json", "summary_metadata.json")
        
        self.index_path = Path(index_path or default_index)
        self.metadata_path = Path(metadata_path or default_metadata)
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        
        # Initialize index and metadata
        self.index: faiss.IndexFlatIP | None = None
        self.metadata: list[SummaryMetadata] = []
        
        # Load existing index if available
        self._load_or_create()
        
        logger.info(
            f"SummaryVectorStore initialized: dimension={self.dimension}, "
            f"vectors={self.index.ntotal if self.index else 0}"
        )
    
    def _ensure_directories(self) -> None:
        """Create directories for index and metadata files."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _create_index(self) -> faiss.IndexFlatIP:
        """Create a new FAISS index."""
        logger.info(f"Creating new summary FAISS index with dimension {self.dimension}")
        return faiss.IndexFlatIP(self.dimension)
    
    def _load_or_create(self) -> None:
        """Load existing index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                self._load()
                return
            except Exception as e:
                logger.error(f"Failed to load summary index: {e}")
                logger.info("Creating new summary index")
        
        self.index = self._create_index()
        self.metadata = []
    
    def _load(self) -> None:
        """Load index and metadata from disk."""
        logger.info(f"Loading summary FAISS index from {self.index_path}")
        self.index = faiss.read_index(str(self.index_path))
        
        logger.info(f"Loading summary metadata from {self.metadata_path}")
        with open(self.metadata_path, "r") as f:
            data = json.load(f)
            self.metadata = [SummaryMetadata.from_dict(m) for m in data]
        
        logger.info(
            f"Loaded {self.index.ntotal} summary vectors with "
            f"{len(self.metadata)} metadata entries"
        )
    
    def save(self) -> None:
        """Save index and metadata to disk."""
        if self.index is None:
            logger.warning("No summary index to save")
            return
        
        self._ensure_directories()
        
        logger.info(f"Saving summary FAISS index to {self.index_path}")
        faiss.write_index(self.index, str(self.index_path))
        
        logger.info(f"Saving summary metadata to {self.metadata_path}")
        with open(self.metadata_path, "w") as f:
            data = [m.to_dict() for m in self.metadata]
            json.dump(data, f)
        
        logger.info(f"Saved {self.index.ntotal} summary vectors")
    
    def add_embedding(
        self,
        embedding: list[float],
        metadata: SummaryMetadata,
    ) -> int:
        """
        Add a single embedding to the index.
        
        Args:
            embedding: Embedding vector.
            metadata: Metadata for the summary.
            
        Returns:
            FAISS index position.
        """
        if self.index is None:
            self.index = self._create_index()
        
        # Convert and normalize
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)
        
        # Get position
        position = self.index.ntotal
        
        # Add to index
        self.index.add(vector)
        self.metadata.append(metadata)
        
        logger.debug(
            f"Added {metadata.summary_type} summary {metadata.summary_id} "
            f"at position {position}"
        )
        
        return position
    
    def add_embeddings(
        self,
        embeddings: list[list[float]],
        metadata_list: list[SummaryMetadata],
    ) -> list[int]:
        """
        Add multiple embeddings to the index.
        
        Args:
            embeddings: List of embedding vectors.
            metadata_list: List of metadata for each embedding.
            
        Returns:
            List of FAISS index positions.
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
        
        # Convert and normalize
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        
        # Get starting position
        start_pos = self.index.ntotal
        
        # Add to index
        self.index.add(vectors)
        self.metadata.extend(metadata_list)
        
        positions = list(range(start_pos, start_pos + len(embeddings)))
        
        logger.info(f"Added {len(embeddings)} summary vectors to index")
        
        return positions
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        summary_type: Literal["topic", "unit"] | None = None,
        user_id: int | None = None,
        subject_id: int | None = None,
        unit_id: int | None = None,
        topic_id: int | None = None,
    ) -> list[SummarySearchResult]:
        """
        Search for similar summaries with metadata filtering.
        
        Args:
            query_embedding: Query embedding vector.
            top_k: Number of results to return.
            summary_type: Filter by summary type.
            user_id: Filter by user ID.
            subject_id: Filter by subject ID.
            unit_id: Filter by unit ID.
            topic_id: Filter by topic ID.
            
        Returns:
            List of SummarySearchResult objects.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Empty summary index, no search results")
            return []
        
        # Convert and normalize query
        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        
        # Over-fetch for filtering
        search_k = min(top_k * 10, self.index.ntotal)
        
        distances, indices = self.index.search(query, search_k)
        
        # Build results with filtering
        results: list[SummarySearchResult] = []
        
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:
                break
            
            meta = self.metadata[idx]
            
            # Apply filters
            if summary_type is not None and meta.summary_type != summary_type:
                continue
            if user_id is not None and meta.user_id != user_id:
                continue
            if subject_id is not None and meta.subject_id != subject_id:
                continue
            if unit_id is not None and meta.unit_id != unit_id:
                continue
            if topic_id is not None and meta.topic_id != topic_id:
                continue
            
            results.append(SummarySearchResult(
                summary_id=meta.summary_id,
                summary_type=meta.summary_type,
                score=float(distance),
                metadata=meta,
            ))
            
            if len(results) >= top_k:
                break
        
        logger.info(f"Summary search returned {len(results)} results")
        
        return results
    
    def get_embedding_id(
        self, 
        summary_id: int, 
        summary_type: Literal["topic", "unit"]
    ) -> int | None:
        """
        Get the FAISS index position for a summary.
        
        Args:
            summary_id: Database summary ID.
            summary_type: Type of summary.
            
        Returns:
            FAISS index position, or None if not found.
        """
        for i, meta in enumerate(self.metadata):
            if meta.summary_id == summary_id and meta.summary_type == summary_type:
                return i
        return None
    
    def has_summary(
        self, 
        summary_id: int, 
        summary_type: Literal["topic", "unit"]
    ) -> bool:
        """Check if a summary is already in the index."""
        return self.get_embedding_id(summary_id, summary_type) is not None
    
    @property
    def size(self) -> int:
        """Get number of vectors in the index."""
        return self.index.ntotal if self.index else 0
    
    def clear(self) -> None:
        """Clear the index and metadata."""
        logger.info("Clearing summary FAISS index")
        self.index = self._create_index()
        self.metadata = []


# Singleton instance
_summary_store: SummaryVectorStore | None = None


def get_summary_vector_store() -> SummaryVectorStore:
    """
    Get the singleton summary vector store instance.
    
    Returns:
        SummaryVectorStore instance.
    """
    global _summary_store
    if _summary_store is None:
        _summary_store = SummaryVectorStore()
    return _summary_store


def reset_summary_vector_store() -> None:
    """Reset the singleton instance (for testing)."""
    global _summary_store
    _summary_store = None
