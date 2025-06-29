"""Retry mechanisms with exponential backoff for API operations."""

import time
import random
import logging
from typing import Callable, Type, Tuple, Union
from functools import wraps
from .exceptions import APIError, APIRateLimitError, APIConnectionError, APITimeoutError


logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (APIConnectionError, APITimeoutError)
):
    """
    Decorator that retries function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        jitter: Whether to add random jitter to delays (default: True)
        retryable_exceptions: Tuple of exception types that should trigger retries
    
    Returns:
        Decorated function that implements retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__}")
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded after {attempt} retries")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this exception should trigger a retry
                    # Always retry rate limit errors
                    if isinstance(e, APIRateLimitError):
                        pass  # Continue to retry logic
                    elif not isinstance(e, retryable_exceptions):
                        logger.debug(f"{func.__name__} failed with non-retryable exception: {e}")
                        raise
                    
                    # Don't retry on final attempt
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    # Calculate delay for exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    # Special handling for rate limit errors
                    if isinstance(e, APIRateLimitError) and hasattr(e, 'retry_after') and e.retry_after:
                        delay = max(delay, e.retry_after)
                        logger.warning(f"{func.__name__} rate limited, waiting {delay} seconds (retry_after: {e.retry_after})")
                    else:
                        logger.warning(f"{func.__name__} failed on attempt {attempt + 1}, retrying in {delay:.2f} seconds: {e}")
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate the delay for exponential backoff.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Initial delay in seconds
        backoff_factor: Multiplier for exponential backoff
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter
    
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
    
    if jitter:
        delay += random.uniform(0, delay * 0.1)
    
    return delay