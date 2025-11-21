"""Schedule repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.infrastructure.database.models import Schedule


class IScheduleRepository(ABC):
    """Abstract interface for schedule persistence operations."""

    @abstractmethod
    async def create(self, schedule: Schedule) -> Schedule:
        """Create a new schedule.
        
        Args:
            schedule: The schedule entity to persist
            
        Returns:
            The created schedule with database-generated fields
        """
        pass

    @abstractmethod
    async def find_by_id(
        self,
        schedule_id: str,
        tenant_id: str,
    ) -> Optional[Schedule]:
        """Find a schedule by ID within a tenant.
        
        Args:
            schedule_id: The schedule unique identifier
            tenant_id: The tenant unique identifier (for multi-tenancy isolation)
            
        Returns:
            The schedule if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_tenant_id(
        self,
        tenant_id: str,
        cursor: Optional[str] = None,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Schedule], Optional[str]]:
        """Find schedules for a tenant with cursor-based pagination.
        
        Args:
            tenant_id: The tenant unique identifier
            cursor: Opaque cursor for pagination (base64-encoded timestamp+id)
            limit: Maximum number of schedules to return (default: 20, max: 100)
            is_active: Filter by active status (None = all schedules)
            
        Returns:
            Tuple of (list of schedules, next_cursor)
            next_cursor is None if no more results
        """
        pass

    @abstractmethod
    async def find_due_schedules(
        self,
        current_time: datetime,
        limit: int = 100,
    ) -> list[Schedule]:
        """Find schedules that are due for execution.
        
        Args:
            current_time: The reference time for finding due schedules
            limit: Maximum number of schedules to return (default: 100)
            
        Returns:
            List of schedules where next_run_at <= current_time and is_active = True
        """
        pass

    @abstractmethod
    async def update(self, schedule: Schedule) -> Schedule:
        """Update an existing schedule.
        
        Args:
            schedule: The schedule entity with updated fields
            
        Returns:
            The updated schedule
        """
        pass

    @abstractmethod
    async def delete(
        self,
        schedule_id: str,
        tenant_id: str,
    ) -> bool:
        """Delete a schedule by ID within a tenant.
        
        Args:
            schedule_id: The schedule unique identifier
            tenant_id: The tenant unique identifier (for multi-tenancy isolation)
            
        Returns:
            True if the schedule was deleted, False if not found
        """
        pass

    @abstractmethod
    async def count_by_tenant_id(
        self,
        tenant_id: str,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count schedules for a tenant.
        
        Args:
            tenant_id: The tenant unique identifier
            is_active: Filter by active status (None = all schedules)
            
        Returns:
            The count of schedules matching the criteria
        """
        pass
