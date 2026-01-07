"""
LLM utilities for text generation.

This module provides OpenAI LLM integration for:
- Summary generation
- Intent classification
- Chat/RAG responses
"""

import logging
from typing import Literal

import openai

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Default model for chat completions
DEFAULT_CHAT_MODEL = "gpt-4o-mini"


class LLMGenerator:
    """
    OpenAI LLM generator for text generation tasks.
    
    Handles chat completions for summarization, classification,
    and RAG responses.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_CHAT_MODEL,
    ):
        """
        Initialize the LLM generator.
        
        Args:
            api_key: OpenAI API key. If None, uses settings.
            model: Chat model name.
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
        
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        
        logger.info(f"LLMGenerator initialized with model: {self.model}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        system_message: str | None = None,
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The user prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0-1).
            system_message: Optional system message.
            
        Returns:
            Generated text.
            
        Raises:
            ValueError: If API key is not configured.
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        logger.debug(f"Generating response with {len(prompt)} char prompt")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        result = response.choices[0].message.content or ""
        
        logger.debug(f"Generated {len(result)} char response")
        
        return result.strip()
    
    def classify_intent(
        self,
        prompt: str,
        valid_intents: list[str],
    ) -> str:
        """
        Classify intent from a prompt.
        
        Args:
            prompt: The classification prompt.
            valid_intents: List of valid intent strings.
            
        Returns:
            The classified intent.
        """
        response = self.generate(
            prompt=prompt,
            max_tokens=50,
            temperature=0.0,
        )
        
        # Clean and validate the response
        intent = response.strip().lower().replace('"', '').replace("'", "")
        
        # Find the best match
        for valid in valid_intents:
            if valid in intent:
                return valid
        
        # Default to explain_detail if no match
        logger.warning(f"Could not classify intent '{response}', defaulting to explain_detail")
        return "explain_detail"
    
    def generate_summary(
        self,
        prompt: str,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate a summary.
        
        Args:
            prompt: The summarization prompt.
            max_tokens: Maximum tokens in summary.
            
        Returns:
            Generated summary.
        """
        return self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.3,
            system_message="You are an expert educational content summarizer.",
        )
    
    def generate_chat_response(
        self,
        prompt: str,
        max_tokens: int = 1500,
    ) -> str:
        """
        Generate a chat response for RAG.
        
        Args:
            prompt: The chat prompt with context.
            max_tokens: Maximum tokens in response.
            
        Returns:
            Generated response.
        """
        return self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.4,
            system_message=(
                "You are a helpful educational tutor. You ONLY answer based on "
                "the provided context. If information is not in the context, "
                "clearly state that it's not found in the uploaded material."
            ),
        )


# Singleton instance
_generator: LLMGenerator | None = None


def get_llm_generator() -> LLMGenerator:
    """
    Get the singleton LLM generator instance.
    
    Returns:
        LLMGenerator instance.
    """
    global _generator
    if _generator is None:
        _generator = LLMGenerator()
    return _generator


def reset_llm_generator() -> None:
    """Reset the singleton instance (for testing)."""
    global _generator
    _generator = None


def generate_text(prompt: str, max_tokens: int = 1000) -> str:
    """Convenience function to generate text."""
    return get_llm_generator().generate(prompt, max_tokens)


def classify_intent(prompt: str, valid_intents: list[str]) -> str:
    """Convenience function to classify intent."""
    return get_llm_generator().classify_intent(prompt, valid_intents)
