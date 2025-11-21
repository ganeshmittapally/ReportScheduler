"""Schedule domain service with business logic."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from src.domain.interfaces.schedule_repository import IScheduleRepository
from src.infrastructure.database.models import Schedule
from src.utils.cron import calculate_next_run, validate_cron_expression


class ScheduleService:
    """Service for schedule business logic and orchestration."""

    # Tier-based quota limits
    SCHEDULE_LIMITS = {
        "standard": 10,
        "premium": 50,
        "enterprise": 200,
    }

    def __init__(self, repository: IScheduleRepository):
        """Initialize service with repository dependency.
        
        Args:
            repository: The schedule repository implementation
        """
        self._repository = repository

    async def create_schedule(
        self,
        tenant_id: str,
        tenant_tier: str,
        report_definition_id: str,
        name: str,
        cron_expression: str,
        timezone: str,
        email_delivery_config: Optional[dict],
        created_by: str,
    ) -> tuple[Optional[Schedule], Optional[str]]:
        """Create a new schedule with validation.
        
        Args:
            tenant_id: The tenant unique identifier
            tenant_tier: The tenant tier (standard/premium/enterprise)
            report_definition_id: The report definition to schedule
            name: The schedule name
            cron_expression: The cron expression (e.g., "0 9 * * *")
            timezone: The timezone string (e.g., "America/New_York")
            email_delivery_config: Optional email configuration with recipients/subject
            created_by: The user ID creating the schedule
            
        Returns:
            Tuple of (created_schedule, error_message)
            error_message is None if successful
        """
        # Check tenant quota
        schedule_limit = self.SCHEDULE_LIMITS.get(tenant_tier, 10)
        current_count = await self._repository.count_by_tenant_id(
            tenant_id=tenant_id,
            is_active=True,
        )
        if current_count >= schedule_limit:
            return None, f"Schedule limit reached ({schedule_limit} for {tenant_tier} tier)"

        # Validate cron expression
        is_valid, error = validate_cron_expression(cron_expression)
        if not is_valid:
            return None, error

        # Calculate next run time
        try:
            next_run_at = calculate_next_run(
                cron_expr=cron_expression,
                tz=timezone,
            )
        except ValueError as e:
            return None, str(e)

        # Create schedule entity
        schedule = Schedule(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            report_definition_id=report_definition_id,
            name=name,
            cron_expression=cron_expression,
            timezone=timezone,
            is_active=True,
            next_run_at=next_run_at,
            email_delivery_config=email_delivery_config,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Persist to database
        created = await self._repository.create(schedule)
        return created, None

    async def get_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
    ) -> Optional[Schedule]:
        """Get a schedule by ID.
        
        Args:
            schedule_id: The schedule unique identifier
            tenant_id: The tenant unique identifier (for multi-tenancy isolation)
            
        Returns:
            The schedule if found, None otherwise
        """
        return await self._repository.find_by_id(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
        )

    async def list_schedules(
        self,
        tenant_id: str,
        cursor: Optional[str] = None,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Schedule], Optional[str]]:
        """List schedules for a tenant with pagination.
        
        Args:
            tenant_id: The tenant unique identifier
            cursor: Opaque cursor for pagination
            limit: Maximum number of schedules to return (default: 20)
            is_active: Filter by active status (None = all schedules)
            
        Returns:
            Tuple of (list of schedules, next_cursor)
        """
        return await self._repository.find_by_tenant_id(
            tenant_id=tenant_id,
            cursor=cursor,
            limit=limit,
            is_active=is_active,
        )

    async def update_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        timezone: Optional[str] = None,
        email_delivery_config: Optional[dict] = None,
    ) -> tuple[Optional[Schedule], Optional[str]]:
        """Update an existing schedule.
        
        Args:
            schedule_id: The schedule unique identifier
            tenant_id: The tenant unique identifier (for multi-tenancy isolation)
            name: New schedule name (optional)
            cron_expression: New cron expression (optional)
            timezone: New timezone (optional)
            email_delivery_config: New email configuration (optional)
            
        Returns:
            Tuple of (updated_schedule, error_message)
            error_message is None if successful
        """
        # Fetch existing schedule
        schedule = await self._repository.find_by_id(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
        )
        if not schedule:
            return None, "Schedule not found"

        # Update fields
        if name is not None:
            schedule.name = name

        # If cron or timezone changes, recalculate next_run_at
        recalculate_next_run = False
        if cron_expression is not None:
            is_valid, error = validate_cron_expression(cron_expression)
            if not is_valid:
                return None, error
            schedule.cron_expression = cron_expression
            recalculate_next_run = True

        if timezone is not None:
            schedule.timezone = timezone
            recalculate_next_run = True

        if recalculate_next_run:
            try:
                schedule.next_run_at = calculate_next_run(
                    cron_expr=schedule.cron_expression,
                    tz=schedule.timezone,
                )
            except ValueError as e:
                return None, str(e)

        if email_delivery_config is not None:
            schedule.email_delivery_config = email_delivery_config

        # Persist changes
        updated = await self._repository.update(schedule)
        return updated, None

    async def delete_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
    ) -> bool:
        """Delete a schedule.
        
        Args:
            schedule_id: The schedule unique identifier
            tenant_id: The tenant unique identifier (for multi-tenancy isolation)
            
        Returns:
            True if deleted, False if not found
        """
        return await self._repository.delete(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
        )

    async def pause_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
    ) -> tuple[Optional[Schedule], Optional[str]]:
        """Pause a schedule (set is_active to False).
        
        Args:
            schedule_id: The schedule unique identifier
            tenant_id: The tenant unique identifier (for multi-tenancy isolation)
            
        Returns:
            Tuple of (updated_schedule, error_message)
        """
        schedule = await self._repository.find_by_id(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
        )
        if not schedule:
            return None, "Schedule not found"

        schedule.is_active = False
        updated = await self._repository.update(schedule)
        return updated, None

    async def resume_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
    ) -> tuple[Optional[Schedule], Optional[str]]:
        """Resume a schedule (set is_active to True and recalculate next_run_at).
        
        Args:
            schedule_id: The schedule unique identifier
            tenant_id: The tenant unique identifier (for multi-tenancy isolation)
            
        Returns:
            Tuple of (updated_schedule, error_message)
        """
        schedule = await self._repository.find_by_id(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
        )
        if not schedule:
            return None, "Schedule not found"

        schedule.is_active = True
        # Recalculate next run time from now
        try:
            schedule.next_run_at = calculate_next_run(
                cron_expr=schedule.cron_expression,
                tz=schedule.timezone,
            )
        except ValueError as e:
            return None, str(e)

        updated = await self._repository.update(schedule)
        return updated, None
