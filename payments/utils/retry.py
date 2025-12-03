"""Retry helpers with optional tenacity support.

Provides a `retry` decorator that retries on Exception with exponential backoff.
If `tenacity` is installed, uses it; otherwise uses a simple custom implementation.
"""
import time
import functools

try:
    from tenacity import retry as tenacity_retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    _HAS_TENACITY = True
except Exception:
    _HAS_TENACITY = False


def retry(max_attempts=3, base_delay=0.5, exceptions=(Exception,)):
    if _HAS_TENACITY:
        def decorator(fn):
            return tenacity_retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=base_delay),
                retry=retry_if_exception_type(exceptions),
            )(fn)
        return decorator

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

