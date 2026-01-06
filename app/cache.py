"""Redis caching utilities for NBA Analytics API."""
import json
import os
from typing import Optional, Any, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Try to import Redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Caching will be disabled. Install with: pip install redis")


class CacheManager:
    """Manages Redis cache connections and operations."""
    
    def __init__(self):
        """Initialize cache manager with Redis connection."""
        self.redis_client = None
        self.enabled = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available. Caching disabled.")
            return
        
        # Get Redis connection details from environment
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,  # Automatically decode responses to strings
                socket_connect_timeout=2,  # 2 second timeout
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"Redis cache connected: {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.enabled = False
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (dict/list) or None if not found/disabled
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                cache_stats.record_miss()
                return None
            # Parse JSON string back to Python object
            cache_stats.record_hit()
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            cache_stats.record_error()
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Serialize to JSON string
            json_value = json.dumps(value)
            # Set with expiration
            self.redis_client.setex(key, ttl, json_value)
            cache_stats.record_set()
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            cache_stats.record_error()
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "player:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern {pattern}: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache entries (use with caution!).
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache clear_all error: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()


class CacheStats:
    """Track cache statistics for performance monitoring."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.errors = 0
        self.total_request_time_with_cache = 0.0
        self.total_request_time_without_cache = 0.0
        self.request_count_with_cache = 0
        self.request_count_without_cache = 0
    
    def record_hit(self, response_time: float = 0.0):
        """Record a cache hit."""
        self.hits += 1
        if response_time > 0:
            self.total_request_time_with_cache += response_time
            self.request_count_with_cache += 1
    
    def record_miss(self, response_time: float = 0.0):
        """Record a cache miss."""
        self.misses += 1
        if response_time > 0:
            self.total_request_time_without_cache += response_time
            self.request_count_without_cache += 1
    
    def record_set(self):
        """Record a cache set operation."""
        self.sets += 1
    
    def record_error(self):
        """Record a cache error."""
        self.errors += 1
    
    def get_stats(self) -> Dict:
        """Get current cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        avg_time_with_cache = (
            self.total_request_time_with_cache / self.request_count_with_cache
            if self.request_count_with_cache > 0 else 0
        )
        avg_time_without_cache = (
            self.total_request_time_without_cache / self.request_count_without_cache
            if self.request_count_without_cache > 0 else 0
        )
        
        speedup = (
            avg_time_without_cache / avg_time_with_cache
            if avg_time_with_cache > 0 and avg_time_without_cache > 0 else 0
        )
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "errors": self.errors,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "avg_response_time_with_cache_ms": round(avg_time_with_cache * 1000, 2),
            "avg_response_time_without_cache_ms": round(avg_time_without_cache * 1000, 2),
            "speedup_factor": round(speedup, 2),
            "time_saved_ms": round((avg_time_without_cache - avg_time_with_cache) * 1000, 2) if avg_time_without_cache > avg_time_with_cache else 0
        }
    
    def reset(self):
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.errors = 0
        self.total_request_time_with_cache = 0.0
        self.total_request_time_without_cache = 0.0
        self.request_count_with_cache = 0
        self.request_count_without_cache = 0


# Global cache statistics
cache_stats = CacheStats()


def cache_key_player_features(player_id: int, season: Optional[str] = None) -> str:
    """Generate cache key for player features."""
    if season:
        return f"player:{player_id}:features:{season}"
    return f"player:{player_id}:features:career"


def cache_key_player_comparison(player_ids: list, season: str) -> str:
    """Generate cache key for player comparison."""
    ids_str = ",".join(sorted(map(str, player_ids)))
    return f"player:compare:{ids_str}:{season}"


def cache_key_team_stats(team_id: int, season: str) -> str:
    """Generate cache key for team stats."""
    return f"team:{team_id}:stats:{season}"


def cache_key_team_comparison(team_ids: list, season: str) -> str:
    """Generate cache key for team comparison."""
    ids_str = ",".join(sorted(map(str, team_ids)))
    return f"team:compare:{ids_str}:{season}"


def cached(ttl: int = 3600, key_func: Optional[callable] = None):
    """Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_func: Function to generate cache key from function arguments
        
    Example:
        @cached(ttl=3600, key_func=lambda player_id, season: f"player:{player_id}:{season}")
        def get_player_stats(player_id, season):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name + args
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator

