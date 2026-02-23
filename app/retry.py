"""
Retry utilities for handling Vertex AI rate limits.

Implements exponential backoff for 429 (Resource Exhausted) errors.
"""

import time
import random
from functools import wraps


def retry_on_429(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """
    Decorator that retries a function on Vertex AI 429 errors with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay cap in seconds

    Usage:
        @retry_on_429(max_retries=3)
        def call_vertex():
            return llm.generate_content(prompt)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()

                    # Check if it's a 429 rate limit error
                    is_429 = (
                        "429" in error_str or
                        "resource exhausted" in error_str or
                        "rate limit" in error_str or
                        "quota" in error_str
                    )

                    if not is_429 or attempt == max_retries:
                        # Not a 429 or out of retries - re-raise
                        raise

                    last_exception = e

                    # Calculate delay with exponential backoff + jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, 0.5) * delay
                    total_delay = delay + jitter

                    print(f"Vertex AI rate limited, retrying in {total_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(total_delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """
    Call a function with retry logic for 429 errors.

    Args:
        func: Callable to execute
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap

    Returns:
        Result of func()

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()

            is_429 = (
                "429" in error_str or
                "resource exhausted" in error_str or
                "rate limit" in error_str or
                "quota" in error_str
            )

            if not is_429 or attempt == max_retries:
                raise

            last_exception = e

            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, 0.5) * delay
            total_delay = delay + jitter

            print(f"Vertex AI rate limited, retrying in {total_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(total_delay)

    if last_exception:
        raise last_exception
