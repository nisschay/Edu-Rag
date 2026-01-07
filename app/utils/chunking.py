"""
Text chunking utilities for RAG processing.

This module provides token-based text chunking with overlap.
Chunks are sized between 300-600 tokens with ~15% overlap.

Uses tiktoken for accurate OpenAI token counting.
"""

import logging
import re
from dataclasses import dataclass
from typing import Iterator

import tiktoken

logger = logging.getLogger(__name__)

# Default chunking parameters
DEFAULT_MIN_CHUNK_SIZE = 300  # tokens
DEFAULT_MAX_CHUNK_SIZE = 600  # tokens
DEFAULT_OVERLAP_PERCENT = 0.15  # 15% overlap

# OpenAI embedding model tokenizer
EMBEDDING_MODEL = "text-embedding-3-small"


@dataclass
class TextChunk:
    """
    Represents a chunk of text with metadata.
    
    Attributes:
        text: The chunk text content.
        chunk_index: Position of this chunk in the source.
        token_count: Number of tokens in this chunk.
        start_char: Starting character position in source text.
        end_char: Ending character position in source text.
    """
    
    text: str
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int


class TextChunker:
    """
    Token-based text chunker with overlap support.
    
    Creates chunks between min_chunk_size and max_chunk_size tokens,
    with specified overlap between consecutive chunks.
    """
    
    def __init__(
        self,
        min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
        max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
        overlap_percent: float = DEFAULT_OVERLAP_PERCENT,
        model: str = EMBEDDING_MODEL,
    ):
        """
        Initialize the chunker.
        
        Args:
            min_chunk_size: Minimum tokens per chunk.
            max_chunk_size: Maximum tokens per chunk.
            overlap_percent: Percentage of overlap (0.0 to 0.5).
            model: Model name for tokenizer selection.
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_percent = overlap_percent
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(
            f"TextChunker initialized: min={min_chunk_size}, max={max_chunk_size}, "
            f"overlap={overlap_percent:.0%}"
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for.
            
        Returns:
            Number of tokens.
        """
        return len(self.encoding.encode(text))
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for natural chunk boundaries.
        
        Args:
            text: Text to split.
            
        Returns:
            List of sentences.
        """
        # Split on sentence boundaries while preserving delimiters
        # Handles: . ! ? followed by space or end of string
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text)
        
        # Filter empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_into_paragraphs(self, text: str) -> list[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Text to split.
            
        Returns:
            List of paragraphs.
        """
        # Split on double newlines or more
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def chunk_text(self, text: str) -> list[TextChunk]:
        """
        Chunk text into overlapping segments.
        
        Creates chunks between min and max token sizes,
        respecting sentence boundaries where possible.
        
        Args:
            text: Text to chunk.
            
        Returns:
            List of TextChunk objects.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # Clean the text
        text = text.strip()
        total_tokens = self.count_tokens(text)
        
        logger.info(f"Chunking text with {total_tokens} total tokens")
        
        # If text is smaller than min chunk size, return as single chunk
        if total_tokens <= self.max_chunk_size:
            logger.info("Text fits in single chunk")
            return [TextChunk(
                text=text,
                chunk_index=0,
                token_count=total_tokens,
                start_char=0,
                end_char=len(text),
            )]
        
        # Split into sentences for natural boundaries
        sentences = self._split_into_sentences(text)
        if not sentences:
            sentences = [text]
        
        chunks: list[TextChunk] = []
        current_sentences: list[str] = []
        current_tokens = 0
        chunk_index = 0
        char_position = 0
        
        # Calculate overlap in tokens
        overlap_tokens = int(self.max_chunk_size * self.overlap_percent)
        target_size = self.max_chunk_size - overlap_tokens
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)
            
            # Handle very long sentences
            if sentence_tokens > self.max_chunk_size:
                # Flush current buffer first
                if current_sentences:
                    chunk_text = " ".join(current_sentences)
                    chunks.append(TextChunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        token_count=current_tokens,
                        start_char=char_position,
                        end_char=char_position + len(chunk_text),
                    ))
                    chunk_index += 1
                    char_position += len(chunk_text) + 1
                    current_sentences = []
                    current_tokens = 0
                
                # Split long sentence by words
                words = sentence.split()
                word_buffer: list[str] = []
                word_tokens = 0
                
                for word in words:
                    wt = self.count_tokens(word + " ")
                    if word_tokens + wt > self.max_chunk_size and word_buffer:
                        chunk_text = " ".join(word_buffer)
                        chunks.append(TextChunk(
                            text=chunk_text,
                            chunk_index=chunk_index,
                            token_count=word_tokens,
                            start_char=char_position,
                            end_char=char_position + len(chunk_text),
                        ))
                        chunk_index += 1
                        char_position += len(chunk_text) + 1
                        
                        # Keep overlap
                        overlap_words = max(1, int(len(word_buffer) * self.overlap_percent))
                        word_buffer = word_buffer[-overlap_words:]
                        word_tokens = self.count_tokens(" ".join(word_buffer))
                    
                    word_buffer.append(word)
                    word_tokens += wt
                
                if word_buffer:
                    current_sentences = [" ".join(word_buffer)]
                    current_tokens = word_tokens
                continue
            
            # Check if adding this sentence exceeds target
            if current_tokens + sentence_tokens > target_size and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    start_char=char_position,
                    end_char=char_position + len(chunk_text),
                ))
                chunk_index += 1
                char_position += len(chunk_text) + 1
                
                # Keep overlap sentences
                overlap_sentence_count = 0
                overlap_token_count = 0
                for j in range(len(current_sentences) - 1, -1, -1):
                    sent_tokens = self.count_tokens(current_sentences[j])
                    if overlap_token_count + sent_tokens <= overlap_tokens:
                        overlap_sentence_count += 1
                        overlap_token_count += sent_tokens
                    else:
                        break
                
                if overlap_sentence_count > 0:
                    current_sentences = current_sentences[-overlap_sentence_count:]
                    current_tokens = overlap_token_count
                else:
                    current_sentences = []
                    current_tokens = 0
            
            current_sentences.append(sentence)
            current_tokens += sentence_tokens
        
        # Add remaining sentences as final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(TextChunk(
                text=chunk_text,
                chunk_index=chunk_index,
                token_count=self.count_tokens(chunk_text),
                start_char=char_position,
                end_char=char_position + len(chunk_text),
            ))
        
        logger.info(f"Created {len(chunks)} chunks from text")
        for i, chunk in enumerate(chunks):
            logger.debug(f"  Chunk {i}: {chunk.token_count} tokens")
        
        return chunks


def chunk_text(
    text: str,
    min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    overlap_percent: float = DEFAULT_OVERLAP_PERCENT,
) -> list[TextChunk]:
    """
    Convenience function to chunk text with default settings.
    
    Args:
        text: Text to chunk.
        min_chunk_size: Minimum tokens per chunk.
        max_chunk_size: Maximum tokens per chunk.
        overlap_percent: Percentage of overlap.
        
    Returns:
        List of TextChunk objects.
    """
    chunker = TextChunker(
        min_chunk_size=min_chunk_size,
        max_chunk_size=max_chunk_size,
        overlap_percent=overlap_percent,
    )
    return chunker.chunk_text(text)
