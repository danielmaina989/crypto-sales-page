"""
Rate limiter for M-Pesa API calls to respect sandbox rate limits.

M-Pesa sandbox allows ~5 requests per 60 seconds. This module provides a distributed
rate limiter using Redis (if available) to coordinate across Celery workers, with a
fallback to in-memory rate limiting for single-process environments.
"""
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import Redis for distributed rate limiting
try:
    import redis
    from redis.exceptions import RedisError
    _HAS_REDIS = True
except Exception:
    _HAS_REDIS = False
    RedisError = Exception


class RateLimiter:
    """Rate limiter that respects M-Pesa sandbox limits: ~5 requests per 60 seconds."""
    
    def __init__(self, name='mpesa_api', requests_per_period=5, period_seconds=60, use_redis=True):
        """
        Args:
            name: Identifier for this rate limiter (e.g., 'mpesa_api')
            requests_per_period: Max requests allowed in the period
            period_seconds: Time window in seconds
            use_redis: Whether to try Redis-backed distribution (requires Redis)
        """
        self.name = name
        self.requests_per_period = requests_per_period
        self.period_seconds = period_seconds
        self.use_redis = use_redis and _HAS_REDIS
        self.redis_client = None
        
        if self.use_redis:
            try:
                # Try to get Redis connection from Celery broker
                broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
                if broker_url and broker_url.startswith('redis://'):
                    self.redis_client = redis.from_url(broker_url, decode_responses=True)
                    self.redis_client.ping()
                    logger.info("RateLimiter: using Redis for distributed rate limiting")
                else:
                    logger.warning("RateLimiter: CELERY_BROKER_URL not set to Redis, falling back to in-memory")
                    self.use_redis = False
            except Exception as e:
                logger.warning("RateLimiter: Redis connection failed, falling back to in-memory: %s", str(e))
                self.use_redis = False
    
    def acquire(self, timeout=0):
        """
        Try to acquire a slot. Blocks up to `timeout` seconds waiting for a slot.
        
        Args:
            timeout: Max seconds to wait (0 = don't wait, negative = infinite)
        
        Returns:
            True if acquired, False if timeout exceeded
        """
        if self.use_redis:
            return self._acquire_redis(timeout)
        else:
            return self._acquire_memory(timeout)
    
    def _acquire_redis(self, timeout):
        """Distributed rate limit using Redis with sliding window."""
        if not self.redis_client:
            return self._acquire_memory(timeout)
        
        key = f"ratelimit:{self.name}"
        now = time.time()
        window_start = now - self.period_seconds
        
        start_time = time.time()
        while True:
            try:
                pipe = self.redis_client.pipeline()
                # Remove old entries outside the window
                pipe.zremrangebyscore(key, 0, window_start)
                # Count current requests in window
                pipe.zcard(key)
                results = pipe.execute()
                count = results[1]
                
                if count < self.requests_per_period:
                    # Add current request timestamp
                    self.redis_client.zadd(key, {str(now): now})
                    # Set expiry to period_seconds so old keys auto-clean
                    self.redis_client.expire(key, self.period_seconds + 1)
                    logger.debug("RateLimiter: acquired (Redis) - %d/%d requests in window", count + 1, self.requests_per_period)
                    return True
                
                # Rate limit exceeded, check timeout
                if timeout == 0:
                    logger.debug("RateLimiter: rate limited (Redis) - %d/%d requests", count, self.requests_per_period)
                    return False
                
                if timeout > 0 and (time.time() - start_time) >= timeout:
                    logger.debug("RateLimiter: timeout exceeded (Redis)")
                    return False
                
                # Wait before retrying
                time.sleep(0.1)
            except RedisError as e:
                logger.warning("RateLimiter: Redis error, falling back to memory: %s", str(e))
                self.use_redis = False
                self.redis_client = None
                return self._acquire_memory(timeout - (time.time() - start_time))
    
    def _acquire_memory(self, timeout):
        """In-memory rate limit (single process only, not distributed)."""
        # Using a simple circular buffer approach
        if not hasattr(self, '_requests'):
            self._requests = []
        
        now = time.time()
        window_start = now - self.period_seconds
        
        # Remove old entries
        self._requests = [t for t in self._requests if t > window_start]
        
        start_time = time.time()
        while len(self._requests) >= self.requests_per_period:
            if timeout == 0:
                logger.debug("RateLimiter: rate limited (memory) - %d/%d requests", len(self._requests), self.requests_per_period)
                return False
            
            if timeout > 0 and (time.time() - start_time) >= timeout:
                logger.debug("RateLimiter: timeout exceeded (memory)")
                return False
            
            # Oldest request in window
            oldest = self._requests[0] if self._requests else now
            sleep_time = max(0.1, oldest + self.period_seconds - now)
            if timeout > 0:
                sleep_time = min(sleep_time, timeout - (time.time() - start_time))
            time.sleep(sleep_time)
            now = time.time()
            window_start = now - self.period_seconds
            self._requests = [t for t in self._requests if t > window_start]
        
        self._requests.append(now)
        logger.debug("RateLimiter: acquired (memory) - %d/%d requests in window", len(self._requests), self.requests_per_period)
        return True


# Global rate limiter instance for M-Pesa API
_mpesa_rate_limiter = None


def get_mpesa_rate_limiter():
    """Get or create the global M-Pesa rate limiter."""
    global _mpesa_rate_limiter
    if _mpesa_rate_limiter is None:
        # M-Pesa sandbox: 5 requests per 60 seconds (with 1 request max burst)
        # Use 1.2x safety factor: allow 4 requests per 60 seconds
        requests = int(getattr(settings, 'MPESA_RATE_LIMIT_REQUESTS', 4))
        period = int(getattr(settings, 'MPESA_RATE_LIMIT_PERIOD', 60))
        _mpesa_rate_limiter = RateLimiter('mpesa_api', requests_per_period=requests, period_seconds=period)
    return _mpesa_rate_limiter


def wait_for_rate_limit():
    """Block until a rate limit slot is available."""
    limiter = get_mpesa_rate_limiter()
    # Wait indefinitely (negative timeout means infinite)
    acquired = limiter.acquire(timeout=-1)
    if not acquired:
        logger.error("RateLimiter: failed to acquire slot (should not happen with infinite timeout)")
    return acquired
