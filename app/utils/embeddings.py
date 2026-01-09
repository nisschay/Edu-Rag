"""
Embedding utilities for RAG processing.

This module provides OpenAI embedding generation for text chunks.
Uses the text-embedding-3-small model by default.
"""

import logging
from typing import Sequence

import google.generativeai as genai

from app.core.config import get_settings
from app.utils.retry_utils import retry_on_exception

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Google Gemini embedding generator.
    
    Generates embeddings for text using Google's generative AI SDK.
    Supports batch processing for efficiency.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize the embedding generator.
        
        Args:
            api_key: Google API key. If None, uses settings.
            model: Embedding model name. If None, uses settings.
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        
        if not self.api_key:
            logger.warning("Gemini API key not configured")
        else:
            genai.configure(api_key=self.api_key)
        
        logger.info(f"EmbeddingGenerator initialized with model: {self.model}")
    
    @retry_on_exception(max_attempts=4, delay=2.0, backoff=2.0, exceptions=(Exception,), rate_limit_delay=30.0)
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text with retry logic and timeout.
        
        Args:
            text: Text to embed.
            
        Returns:
            Embedding vector as list of floats.
            
        Raises:
            ValueError: If API key is not configured.
        """
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        if not text or not text.strip():
            raise ValueError("Empty text cannot be embedded")
        
        logger.debug(f"Embedding text of length {len(text)}")
        
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )
        
        embedding = result['embedding']
        logger.debug(f"Generated embedding with dimension {len(embedding)}")
        
        return embedding
    
    @retry_on_exception(max_attempts=4, delay=2.0, backoff=2.0, exceptions=(Exception,), rate_limit_delay=30.0)
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batch.
        """
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if len(valid_texts) != len(texts):
            logger.warning(
                f"Filtered {len(texts) - len(valid_texts)} empty texts from batch"
            )
        
        if not valid_texts:
            return []
        
        logger.info(f"Embedding batch of {len(valid_texts)} texts")
        
        # Google SDK supports batching natively
        result = genai.embed_content(
            model=self.model,
            content=valid_texts,
            task_type="retrieval_document",
        )
        
        embeddings = result['embedding']
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        return embeddings


# Singleton instance for convenience
_generator: EmbeddingGenerator | None = None


def get_embedding_generator() -> EmbeddingGenerator:
    """
    Get the singleton embedding generator instance.
    
    Returns:
        EmbeddingGenerator instance.
    """
    global _generator
    if _generator is None:
        _generator = EmbeddingGenerator()
    return _generator


def embed_text(text: str) -> list[float]:
    """
    Convenience function to embed a single text.
    
    Args:
        text: Text to embed.
        
    Returns:
        Embedding vector.
    """
    return get_embedding_generator().embed_text(text)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """
    Convenience function to embed multiple texts.
    
    Args:
        texts: List of texts to embed.
        
    Returns:
        List of embedding vectors.
    """
    return get_embedding_generator().embed_texts(texts)
