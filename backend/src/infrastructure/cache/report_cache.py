"""Report caching service using Redis for performance optimization."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from redis.asyncio import Redis

from src.config import settings

logger = logging.getLogger(__name__)


class ReportCacheService:
    """Service for caching report generation results.
    
    Caches are keyed by a hash of:
    - Report definition ID
    - Query parameters
    - Date range parameters
    
    This prevents redundant query execution and PDF generation for identical reports.
    """
    
    DEFAULT_TTL_SECONDS = 3600  # 1 hour default
    CACHE_KEY_PREFIX = "report_cache:"
    METADATA_SUFFIX = ":meta"
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize report cache service.
        
        Args:
            redis_client: Optional Redis client (creates new one if not provided)
        """
        self._redis = redis_client
    
    async def _get_redis(self) -> Redis:
        """Get or create Redis client."""
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # We'll handle bytes for PDF content
            )
        return self._redis
    
    def _generate_cache_key(
        self,
        report_definition_id: str,
        query_parameters: Optional[dict] = None,
        date_range: Optional[dict] = None,
    ) -> str:
        """Generate cache key from report parameters.
        
        Args:
            report_definition_id: The report definition ID
            query_parameters: Query parameters (e.g., filters, limits)
            date_range: Date range parameters (e.g., start_date, end_date)
            
        Returns:
            Cache key string
        """
        # Create deterministic hash of parameters
        cache_data = {
            "report_definition_id": report_definition_id,
            "query_parameters": query_parameters or {},
            "date_range": date_range or {},
        }
        
        # Sort keys for deterministic JSON serialization
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_json.encode()).hexdigest()
        
        return f"{self.CACHE_KEY_PREFIX}{cache_hash}"
    
    async def get_cached_report(
        self,
        report_definition_id: str,
        query_parameters: Optional[dict] = None,
        date_range: Optional[dict] = None,
    ) -> Optional[dict]:
        """Retrieve cached report if available.
        
        Args:
            report_definition_id: The report definition ID
            query_parameters: Query parameters
            date_range: Date range parameters
            
        Returns:
            Dict with pdf_bytes and metadata, or None if not cached
        """
        redis = await self._get_redis()
        cache_key = self._generate_cache_key(
            report_definition_id, query_parameters, date_range
        )
        
        try:
            # Check if cache exists
            pdf_bytes = await redis.get(cache_key)
            if pdf_bytes is None:
                logger.debug(f"Cache miss for key: {cache_key}")
                return None
            
            # Get metadata
            meta_key = f"{cache_key}{self.METADATA_SUFFIX}"
            meta_json = await redis.get(meta_key)
            metadata = json.loads(meta_json) if meta_json else {}
            
            logger.info(
                f"Cache hit for report {report_definition_id}",
                extra={
                    "cache_key": cache_key,
                    "cached_at": metadata.get("cached_at"),
                    "size_bytes": len(pdf_bytes),
                },
            )
            
            return {
                "pdf_bytes": pdf_bytes,
                "metadata": metadata,
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached report: {e}", exc_info=True)
            return None
    
    async def cache_report(
        self,
        report_definition_id: str,
        pdf_bytes: bytes,
        query_parameters: Optional[dict] = None,
        date_range: Optional[dict] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Cache a generated report.
        
        Args:
            report_definition_id: The report definition ID
            pdf_bytes: The generated PDF content
            query_parameters: Query parameters
            date_range: Date range parameters
            ttl_seconds: Time-to-live in seconds (default: DEFAULT_TTL_SECONDS)
            metadata: Optional metadata to store with cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        redis = await self._get_redis()
        cache_key = self._generate_cache_key(
            report_definition_id, query_parameters, date_range
        )
        
        ttl = ttl_seconds or self.DEFAULT_TTL_SECONDS
        
        try:
            # Store PDF bytes
            await redis.setex(cache_key, ttl, pdf_bytes)
            
            # Store metadata
            cache_metadata = {
                "report_definition_id": report_definition_id,
                "cached_at": datetime.utcnow().isoformat(),
                "size_bytes": len(pdf_bytes),
                "ttl_seconds": ttl,
                **(metadata or {}),
            }
            meta_key = f"{cache_key}{self.METADATA_SUFFIX}"
            await redis.setex(meta_key, ttl, json.dumps(cache_metadata))
            
            logger.info(
                f"Cached report {report_definition_id}",
                extra={
                    "cache_key": cache_key,
                    "size_bytes": len(pdf_bytes),
                    "ttl_seconds": ttl,
                },
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache report: {e}", exc_info=True)
            return False
    
    async def invalidate_report(
        self,
        report_definition_id: str,
        query_parameters: Optional[dict] = None,
        date_range: Optional[dict] = None,
    ) -> bool:
        """Invalidate a cached report.
        
        Args:
            report_definition_id: The report definition ID
            query_parameters: Query parameters
            date_range: Date range parameters
            
        Returns:
            True if invalidated successfully
        """
        redis = await self._get_redis()
        cache_key = self._generate_cache_key(
            report_definition_id, query_parameters, date_range
        )
        
        try:
            meta_key = f"{cache_key}{self.METADATA_SUFFIX}"
            deleted_count = await redis.delete(cache_key, meta_key)
            
            logger.info(
                f"Invalidated cache for report {report_definition_id}",
                extra={
                    "cache_key": cache_key,
                    "deleted_count": deleted_count,
                },
            )
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}", exc_info=True)
            return False
    
    async def invalidate_all_for_report(self, report_definition_id: str) -> int:
        """Invalidate all cached versions of a report definition.
        
        Useful when report definition is updated and all cached versions
        should be invalidated.
        
        Args:
            report_definition_id: The report definition ID
            
        Returns:
            Number of cache entries deleted
        """
        redis = await self._get_redis()
        
        try:
            # Find all keys matching this report definition
            # Note: This is a simple implementation. For production, consider
            # maintaining a separate index of cache keys per report definition.
            pattern = f"{self.CACHE_KEY_PREFIX}*"
            deleted_count = 0
            
            async for key in redis.scan_iter(match=pattern, count=100):
                # Check metadata to see if it matches report definition
                if key.endswith(self.METADATA_SUFFIX.encode()):
                    meta_json = await redis.get(key)
                    if meta_json:
                        metadata = json.loads(meta_json)
                        if metadata.get("report_definition_id") == report_definition_id:
                            # Delete both metadata and PDF
                            pdf_key = key[: -len(self.METADATA_SUFFIX)]
                            await redis.delete(pdf_key, key)
                            deleted_count += 1
            
            logger.info(
                f"Invalidated {deleted_count} cache entries for report {report_definition_id}",
                extra={
                    "report_definition_id": report_definition_id,
                    "deleted_count": deleted_count,
                },
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate all caches: {e}", exc_info=True)
            return 0
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        redis = await self._get_redis()
        
        try:
            pattern = f"{self.CACHE_KEY_PREFIX}*"
            total_keys = 0
            total_size_bytes = 0
            
            async for key in redis.scan_iter(match=pattern, count=100):
                if not key.endswith(self.METADATA_SUFFIX.encode()):
                    total_keys += 1
                    # Get size of cached PDF
                    size = await redis.strlen(key)
                    total_size_bytes += size
            
            return {
                "total_cached_reports": total_keys,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / 1024 / 1024, 2),
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}", exc_info=True)
            return {
                "total_cached_reports": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
            }
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
