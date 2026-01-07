"""
Embedding utilities for RAG processing.

This module provides OpenAI embedding generation for text chunks.
Uses the text-embedding-3-small model by default.
"""

import logging
from typing import Sequence

import openai

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    OpenAI embedding generator.
    
    Generates embeddings for text using OpenAI's embedding API.
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
            api_key: OpenAI API key. If None, uses settings.
            model: Embedding model name. If None, uses settings.
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
        
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        
        logger.info(f"EmbeddingGenerator initialized with model: {self.model}")
    
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed.
            
        Returns:
            Embedding vector as list of floats.
            
        Raises:
            ValueError: If API key is not configured.
            openai.OpenAIError: If API call fails.
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        if not text or not text.strip():
            raise ValueError("Empty text cannot be embedded")
        
        logger.debug(f"Embedding text of length {len(text)}")
        
        response = self.client.embeddings.create(
            input=text,
            model=self.model,
        )
        
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding with dimension {len(embedding)}")
        
        return embedding
    
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        OpenAI's API supports batch embedding for efficiency.
        
        Args:
            texts: List of texts to embed.
            
        Returns:
            List of embedding vectors.
            
        Raises:
            ValueError: If API key is not configured.
            openai.OpenAIError: If API call fails.
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
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
        
        # OpenAI recommends batches of up to 2048 inputs
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            logger.debug(f"Processing batch {i // batch_size + 1}")
            
            response = self.client.embeddings.create(
                input=batch,
                model=self.model,
            )
            
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            batch_embeddings = [d.embedding for d in sorted_data]
            all_embeddings.extend(batch_embeddings)
        
        logger.info(f"Generated {len(all_embeddings)} embeddings")
        
        return all_embeddings


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
