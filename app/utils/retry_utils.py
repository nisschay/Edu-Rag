"""
Simple retry utilities for API calls.
"""

import time
import logging
import functools
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry_on_exception(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function call on specific exceptions.
    
    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for exponential backoff.
        exceptions: Tuple of exception classes to catch.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {attempts} attempts: {e}")
                        raise e
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempts}/{max_attempts}). "
                        f"Retrying in {current_delay}s... Error: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None # Should not reach here
        return wrapper
    return decorator
