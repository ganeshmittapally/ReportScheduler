"""PostgreSQL implementation of the schedule repository."""

import base64
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.interfaces.schedule_repository import IScheduleRepository
from src.infrastructure.database.models import Schedule


class PostgresScheduleRepository(IScheduleRepository):
    """Concrete implementation of schedule repository using PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: The async SQLAlchemy session
        """
        self._session = session

    async def create(self, schedule: Schedule) -> Schedule:
        """Create a new schedule.
        
        Args:
            schedule: The schedule entity to persist
            
        Returns:
            The created schedule with database-generated fields
        """
        self._session.add(schedule)
        await self._session.flush()  # Populate generated fields
        await self._session.refresh(schedule)  # Load relationships
        return schedule

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
        stmt = (
            select(Schedule)
            .where(
                and_(
                    Schedule.id == schedule_id,
                    Schedule.tenant_id == tenant_id,
                )
            )
            .options(
                selectinload(Schedule.report_definition),
                selectinload(Schedule.tenant),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

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
        # Enforce max limit
        limit = min(limit, 100)

        # Build base query
        conditions = [Schedule.tenant_id == tenant_id]
        if is_active is not None:
            conditions.append(Schedule.is_active == is_active)

        # Decode cursor for pagination
        cursor_created_at: Optional[datetime] = None
        cursor_id: Optional[str] = None
        if cursor:
            try:
                decoded = base64.b64decode(cursor).decode("utf-8")
                cursor_data = json.loads(decoded)
                cursor_created_at = datetime.fromisoformat(cursor_data["created_at"])
                cursor_id = cursor_data["id"]
                conditions.append(
                    or_(
                        Schedule.created_at < cursor_created_at,
                        and_(
                            Schedule.created_at == cursor_created_at,
                            Schedule.id < cursor_id,
                        ),
                    )
                )
            except (ValueError, KeyError, json.JSONDecodeError):
                # Invalid cursor, ignore and return from start
                pass

        # Execute query with one extra row to check if more results exist
        stmt = (
            select(Schedule)
            .where(and_(*conditions))
            .order_by(Schedule.created_at.desc(), Schedule.id.desc())
            .limit(limit + 1)
            .options(selectinload(Schedule.report_definition))
        )

        result = await self._session.execute(stmt)
        schedules = list(result.scalars().all())

        # Calculate next cursor
        next_cursor: Optional[str] = None
        if len(schedules) > limit:
            schedules = schedules[:limit]  # Remove the extra row
            last_schedule = schedules[-1]
            cursor_data = {
                "created_at": last_schedule.created_at.isoformat(),
                "id": last_schedule.id,
            }
            next_cursor = base64.b64encode(
                json.dumps(cursor_data).encode("utf-8")
            ).decode("utf-8")

        return schedules, next_cursor

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
        stmt = (
            select(Schedule)
            .where(
                and_(
                    Schedule.is_active == True,  # noqa: E712
                    Schedule.next_run_at <= current_time,
                    Schedule.next_run_at.is_not(None),
                )
            )
            .order_by(Schedule.next_run_at.asc())
            .limit(limit)
            .options(
                selectinload(Schedule.report_definition),
                selectinload(Schedule.tenant),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, schedule: Schedule) -> Schedule:
        """Update an existing schedule.
        
        Args:
            schedule: The schedule entity with updated fields
            
        Returns:
            The updated schedule
        """
        schedule.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(schedule)
        return schedule

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
        stmt = delete(Schedule).where(
            and_(
                Schedule.id == schedule_id,
                Schedule.tenant_id == tenant_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

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
        conditions = [Schedule.tenant_id == tenant_id]
        if is_active is not None:
            conditions.append(Schedule.is_active == is_active)

        stmt = select(func.count()).select_from(Schedule).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar_one()
