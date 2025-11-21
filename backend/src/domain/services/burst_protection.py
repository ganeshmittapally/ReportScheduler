"""Burst protection service to prevent resource exhaustion."""

import logging
from datetime import datetime, timezone
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.infrastructure.database.models import ExecutionRun

logger = logging.getLogger(__name__)


class BurstProtectionService:
    """Service to enforce concurrency limits and prevent resource exhaustion."""
    
    # Default limits
    DEFAULT_MAX_CONCURRENT_PER_TENANT = 5
    DEFAULT_MAX_CONCURRENT_GLOBAL = 50
    
    LOCK_PREFIX = "burst_protection:"
    COUNTER_PREFIX = "concurrent_executions:"
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize burst protection service.
        
        Args:
            redis_client: Optional Redis client
        """
        self._redis = redis_client
    
    async def _get_redis(self) -> Redis:
        """Get or create Redis client."""
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis
    
    async def check_can_execute(
        self,
        tenant_id: str,
        max_concurrent_per_tenant: Optional[int] = None,
        max_concurrent_global: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """Check if a new execution can be started.
        
        Args:
            tenant_id: The tenant ID
            max_concurrent_per_tenant: Max concurrent executions per tenant
            max_concurrent_global: Max concurrent executions globally
            
        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        redis = await self._get_redis()
        
        max_tenant = max_concurrent_per_tenant or self.DEFAULT_MAX_CONCURRENT_PER_TENANT
        max_global = max_concurrent_global or self.DEFAULT_MAX_CONCURRENT_GLOBAL
        
        try:
            # Check tenant limit
            tenant_key = f"{self.COUNTER_PREFIX}tenant:{tenant_id}"
            tenant_count = await redis.get(tenant_key)
            tenant_running = int(tenant_count) if tenant_count else 0
            
            if tenant_running >= max_tenant:
                reason = (
                    f"Tenant {tenant_id} has reached max concurrent executions "
                    f"({tenant_running}/{max_tenant})"
                )
                logger.warning(reason)
                return False, reason
            
            # Check global limit
            global_key = f"{self.COUNTER_PREFIX}global"
            global_count = await redis.get(global_key)
            global_running = int(global_count) if global_count else 0
            
            if global_running >= max_global:
                reason = (
                    f"Global max concurrent executions reached "
                    f"({global_running}/{max_global})"
                )
                logger.warning(reason)
                return False, reason
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to check burst protection: {e}", exc_info=True)
            # Fail open - allow execution if check fails
            return True, None
    
    async def increment_execution_count(self, tenant_id: str) -> None:
        """Increment execution counters when starting an execution.
        
        Args:
            tenant_id: The tenant ID
        """
        redis = await self._get_redis()
        
        try:
            tenant_key = f"{self.COUNTER_PREFIX}tenant:{tenant_id}"
            global_key = f"{self.COUNTER_PREFIX}global"
            
            # Increment counters
            await redis.incr(tenant_key)
            await redis.incr(global_key)
            
            # Set expiry to prevent stale counters (1 hour)
            await redis.expire(tenant_key, 3600)
            await redis.expire(global_key, 3600)
            
            logger.debug(f"Incremented execution count for tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to increment execution count: {e}", exc_info=True)
    
    async def decrement_execution_count(self, tenant_id: str) -> None:
        """Decrement execution counters when completing an execution.
        
        Args:
            tenant_id: The tenant ID
        """
        redis = await self._get_redis()
        
        try:
            tenant_key = f"{self.COUNTER_PREFIX}tenant:{tenant_id}"
            global_key = f"{self.COUNTER_PREFIX}global"
            
            # Decrement counters (but not below 0)
            tenant_count = await redis.get(tenant_key)
            if tenant_count and int(tenant_count) > 0:
                await redis.decr(tenant_key)
            
            global_count = await redis.get(global_key)
            if global_count and int(global_count) > 0:
                await redis.decr(global_key)
            
            logger.debug(f"Decremented execution count for tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to decrement execution count: {e}", exc_info=True)
    
    async def get_current_counts(
        self, tenant_id: Optional[str] = None
    ) -> dict:
        """Get current execution counts.
        
        Args:
            tenant_id: Optional tenant ID to get specific tenant count
            
        Returns:
            Dict with current counts
        """
        redis = await self._get_redis()
        
        try:
            result = {}
            
            # Get global count
            global_key = f"{self.COUNTER_PREFIX}global"
            global_count = await redis.get(global_key)
            result["global_running"] = int(global_count) if global_count else 0
            
            # Get tenant count if specified
            if tenant_id:
                tenant_key = f"{self.COUNTER_PREFIX}tenant:{tenant_id}"
                tenant_count = await redis.get(tenant_key)
                result["tenant_running"] = int(tenant_count) if tenant_count else 0
                result["tenant_id"] = tenant_id
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get execution counts: {e}", exc_info=True)
            return {"global_running": 0, "tenant_running": 0}
    
    async def get_running_executions_from_db(
        self,
        session: AsyncSession,
        tenant_id: Optional[str] = None,
    ) -> list[ExecutionRun]:
        """Get currently running executions from database.
        
        This is a fallback method to verify Redis counters.
        
        Args:
            session: Database session
            tenant_id: Optional tenant ID to filter by
            
        Returns:
            List of running ExecutionRun records
        """
        try:
            query = select(ExecutionRun).where(
                ExecutionRun.status.in_(["pending", "running"])
            )
            
            if tenant_id:
                query = query.where(ExecutionRun.tenant_id == tenant_id)
            
            result = await session.execute(query)
            executions = result.scalars().all()
            
            return list(executions)
            
        except Exception as e:
            logger.error(f"Failed to get running executions from DB: {e}", exc_info=True)
            return []
    
    async def sync_counters_with_db(self, session: AsyncSession) -> dict:
        """Sync Redis counters with actual database state.
        
        This can be run periodically to correct any drift between Redis and DB.
        
        Args:
            session: Database session
            
        Returns:
            Dict with sync results
        """
        redis = await self._get_redis()
        
        try:
            # Get actual running count from database
            query = select(
                ExecutionRun.tenant_id,
                func.count(ExecutionRun.id).label("count"),
            ).where(
                ExecutionRun.status.in_(["pending", "running"])
            ).group_by(
                ExecutionRun.tenant_id
            )
            
            result = await session.execute(query)
            tenant_counts = {row.tenant_id: row.count for row in result}
            
            # Update Redis counters
            for tenant_id, count in tenant_counts.items():
                tenant_key = f"{self.COUNTER_PREFIX}tenant:{tenant_id}"
                await redis.set(tenant_key, count, ex=3600)
            
            # Update global count
            total_running = sum(tenant_counts.values())
            global_key = f"{self.COUNTER_PREFIX}global"
            await redis.set(global_key, total_running, ex=3600)
            
            logger.info(
                f"Synced burst protection counters: {len(tenant_counts)} tenants, "
                f"{total_running} total running"
            )
            
            return {
                "tenants_synced": len(tenant_counts),
                "total_running": total_running,
                "tenant_counts": tenant_counts,
            }
            
        except Exception as e:
            logger.error(f"Failed to sync counters with DB: {e}", exc_info=True)
            return {"tenants_synced": 0, "total_running": 0}
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
