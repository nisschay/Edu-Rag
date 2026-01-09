"""
LLM utilities for text generation.

This module provides OpenAI LLM integration for:
- Summary generation
- Intent classification
- Chat/RAG responses
"""

import logging
from typing import Literal

import google.generativeai as genai

from app.core.config import get_settings
from app.utils.retry_utils import retry_on_exception

logger = logging.getLogger(__name__)

# Default model for Google Gemini
DEFAULT_CHAT_MODEL = "gemini-2.5-flash" 


class LLMGenerator:
    """
    Google Gemini LLM generator for text generation tasks.
    
    Handles content generation for summarization, classification,
    and RAG responses.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize the LLM generator.
        
        Args:
            api_key: Google API key. If None, uses settings.
            model: Model name.
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        
        if not self.api_key:
            logger.warning("Gemini API key not configured")
        else:
            genai.configure(api_key=self.api_key)
        
        logger.info(f"LLMGenerator initialized with model: {self.model_name}")
    
    @retry_on_exception(max_attempts=4, delay=2.0, backoff=2.0, exceptions=(Exception,), rate_limit_delay=30.0)
    def _generate_content_with_retry(
        self,
        full_prompt: str,
        generation_config: genai.types.GenerationConfig,
        safety_settings: dict,
    ):
        """Internal method to call Gemini with retry logic."""
        model = genai.GenerativeModel(model_name=self.model_name)
        return model.generate_content(
            full_prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        system_message: str | None = None,
    ) -> str:
        """
        Generate text using Gemini with retry logic and timeout.
        
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
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Build combined prompt if system_message is provided
        full_prompt = prompt
        if system_message:
            full_prompt = f"System Instruction: {system_message}\n\nUser Message: {prompt}"
        
        # Configure safety settings to be more permissive for educational context
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
        
        logger.debug(f"Generating Gemini response with {len(full_prompt)} char prompt")
        
        try:
            response = self._generate_content_with_retry(
                full_prompt=full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            
            try:
                result = response.text or ""
            except (ValueError, Exception) as e:
                logger.warning(f"Gemini response blocked or failed: {e}")
                # Check if there are candidates but blocked
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    logger.warning(f"Finish reason: {candidate.finish_reason}")
                return "I apologize, but I cannot provide a response to that query based on the current material."
                
            logger.debug(f"Generated {len(result)} char response")
            return result.strip()
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Gemini API Error after retries: {error_str}")
            
            # Rate Limit Handling (429)
            if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                return "The system is busy. Please try again later."
            
            # General Error Fallback
            return "I apologize, but I am unable to process your request at the moment due to a system error."
    
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
