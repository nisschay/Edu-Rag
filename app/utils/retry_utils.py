"""
Retry utilities for API calls with rate limit handling.

Provides exponential backoff with jitter and special handling for
rate limit (429) errors to minimize wasted API calls.
"""

import time
import logging
import functools
import random
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Rate limiting state - shared across all API calls
_last_request_time: float = 0
_min_request_interval: float = 0.15  # Minimum 150ms between requests


def _apply_rate_limit():
    """Apply minimum delay between API requests to avoid rate limits."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _min_request_interval:
        time.sleep(_min_request_interval - elapsed)
    _last_request_time = time.time()


def _is_rate_limit_error(exception: Exception) -> bool:
    """Check if the exception is a rate limit error (429)."""
    error_str = str(exception).lower()
    return any(indicator in error_str for indicator in [
        '429', 'resourceexhausted', 'quota', 'rate limit', 'too many requests'
    ])


def _is_bad_request_error(exception: Exception) -> bool:
    """Check if the exception is a 400 bad request that shouldn't be retried."""
    error_str = str(exception).lower()
    # Only skip retry if it's clearly a malformed request, not a quota issue
    return '400' in error_str and any(x in error_str for x in ['invalid', 'malformed', 'bad request'])


def retry_on_exception(
    max_attempts: int = 4,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    rate_limit_delay: float = 30.0,
    max_delay: float = 120.0,
):
    """
    Decorator to retry a function call on specific exceptions.
    
    Features:
    - Exponential backoff with jitter to prevent thundering herd
    - Special handling for rate limit errors (429) with longer delays
    - Pre-request rate limiting to stay under quotas
    - Skips retry for clearly invalid requests (400)
    
    Args:
        max_attempts: Maximum number of attempts (default: 4).
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for exponential backoff.
        exceptions: Tuple of exception classes to catch.
        rate_limit_delay: Base delay for rate limit errors (429).
        max_delay: Maximum delay between retries.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                # Apply rate limiting before each request
                _apply_rate_limit()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except exceptions as e:
                    attempts += 1
                    
                    # Don't retry clearly malformed requests
                    if _is_bad_request_error(e):
                        logger.error(f"Function {func.__name__} got bad request error, not retrying: {e}")
                        raise e
                    
                    if attempts >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {attempts} attempts: {e}")
                        raise e
                    
                    # Special handling for rate limit errors (429)
                    if _is_rate_limit_error(e):
                        # Use longer delay with jitter for rate limits
                        jitter = random.uniform(5, 15)
                        wait_time = rate_limit_delay + jitter
                        logger.warning(
                            f"Rate limit hit for {func.__name__}. "
                            f"Waiting {wait_time:.1f}s before retry {attempts}/{max_attempts}..."
                        )
                        time.sleep(wait_time)
                        # Increase delay for subsequent rate limit errors
                        rate_limit_delay_next = min(rate_limit_delay * 1.5, max_delay)
                    else:
                        # Normal exponential backoff with jitter
                        jitter = random.uniform(0, current_delay * 0.3)
                        wait_time = min(current_delay + jitter, max_delay)
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempts}/{max_attempts}). "
                            f"Retrying in {wait_time:.1f}s... Error: {e}"
                        )
                        time.sleep(wait_time)
                        current_delay = min(current_delay * backoff, max_delay)
                        
            return None  # Should not reach here
        return wrapper
    return decorator


def set_rate_limit_interval(interval: float):
    """
    Set the minimum interval between API requests.
    
    Args:
        interval: Minimum seconds between requests.
    """
    global _min_request_interval
    _min_request_interval = interval
    logger.info(f"Rate limit interval set to {interval}s")
