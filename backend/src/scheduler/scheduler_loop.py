"""APScheduler service for evaluating and triggering scheduled reports."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.infrastructure.database.repositories.postgres_schedule_repository import (
    PostgresScheduleRepository,
)
from src.utils.cron import calculate_next_run

logger = logging.getLogger(__name__)


class SchedulerLoop:
    """Service for evaluating schedules and enqueuing report generation tasks."""

    LOCK_TTL_SECONDS = 60  # Redis lock TTL
    SCAN_INTERVAL_SECONDS = 30  # Poll database every 30 seconds
    BATCH_SIZE = 100  # Max schedules to process per scan

    def __init__(
        self,
        database_url: str,
        redis_url: str,
    ):
        """Initialize scheduler loop with dependencies.
        
        Args:
            database_url: Async PostgreSQL connection string
            redis_url: Redis connection string for distributed locking
        """
        self._database_url = database_url
        self._redis_url = redis_url
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._redis: Optional[Redis] = None
        self._engine = None
        self._session_maker = None

    async def start(self) -> None:
        """Start the scheduler loop."""
        logger.info("Starting scheduler loop")

        # Initialize database connection
        self._engine = create_async_engine(
            self._database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )
        self._session_maker = sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Initialize Redis connection
        self._redis = Redis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

        # Initialize APScheduler
        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._scan_and_trigger,
            trigger=IntervalTrigger(seconds=self.SCAN_INTERVAL_SECONDS),
            id="schedule_scanner",
            name="Scan and trigger due schedules",
            max_instances=1,
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(f"Scheduler loop started (scan interval: {self.SCAN_INTERVAL_SECONDS}s)")

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        logger.info("Stopping scheduler loop")

        if self._scheduler:
            self._scheduler.shutdown(wait=True)

        if self._redis:
            await self._redis.close()

        if self._engine:
            await self._engine.dispose()

        logger.info("Scheduler loop stopped")

    async def _scan_and_trigger(self) -> None:
        """Scan for due schedules and enqueue report generation tasks."""
        lock_key = "scheduler:scan_lock"
        lock_value = f"{asyncio.current_task().get_name()}_{datetime.now().timestamp()}"

        # Acquire distributed lock to prevent duplicate processing
        acquired = await self._redis.set(
            lock_key,
            lock_value,
            nx=True,
            ex=self.LOCK_TTL_SECONDS,
        )

        if not acquired:
            logger.debug("Another scheduler instance is running, skipping scan")
            return

        try:
            start_time = datetime.now(timezone.utc)
            logger.info(f"Starting schedule scan at {start_time.isoformat()}")

            async with self._session_maker() as session:
                repository = PostgresScheduleRepository(session)

                # Find schedules that are due
                due_schedules = await repository.find_due_schedules(
                    current_time=start_time,
                    limit=self.BATCH_SIZE,
                )

                if not due_schedules:
                    logger.debug("No due schedules found")
                    return

                logger.info(f"Found {len(due_schedules)} due schedules")

                # Process each schedule
                for schedule in due_schedules:
                    try:
                        await self._trigger_schedule(schedule, session)
                    except Exception as e:
                        logger.error(
                            f"Failed to trigger schedule {schedule.id}: {e}",
                            exc_info=True,
                            extra={
                                "schedule_id": schedule.id,
                                "tenant_id": schedule.tenant_id,
                            },
                        )

                # Commit all schedule updates
                await session.commit()

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"Schedule scan completed in {duration:.2f}s, "
                f"triggered {len(due_schedules)} schedules"
            )

            # TODO: Emit metrics
            # await metrics.histogram("scheduler_scan_duration_seconds", duration)
            # await metrics.counter("schedules_triggered_total", len(due_schedules))

        except Exception as e:
            logger.error(f"Schedule scan failed: {e}", exc_info=True)
        finally:
            # Release lock
            await self._redis.delete(lock_key)

    async def _trigger_schedule(
        self,
        schedule,
        session: AsyncSession,
    ) -> None:
        """Trigger a single schedule by enqueuing a Celery task.
        
        Args:
            schedule: The schedule to trigger
            session: Database session for updating schedule
        """
        logger.info(
            f"Triggering schedule {schedule.id} ({schedule.name})",
            extra={
                "schedule_id": schedule.id,
                "tenant_id": schedule.tenant_id,
                "report_definition_id": schedule.report_definition_id,
            },
        )

        # Check burst protection before enqueuing
        try:
            from src.domain.services.burst_protection import BurstProtectionService
            
            burst_protection = BurstProtectionService()
            can_execute, reason = await burst_protection.check_can_execute(
                tenant_id=schedule.tenant_id,
            )
            
            if not can_execute:
                logger.warning(
                    f"Skipping schedule {schedule.id} due to burst protection: {reason}",
                    extra={
                        "schedule_id": schedule.id,
                        "tenant_id": schedule.tenant_id,
                        "reason": reason,
                    },
                )
                # Don't update schedule timestamps - will retry next scan
                return
            
        except Exception as e:
            logger.error(
                f"Burst protection check failed for schedule {schedule.id}: {e}",
                exc_info=True,
            )
            # Continue with enqueue if burst protection check fails

        # Enqueue Celery task for report generation
        try:
            from src.workers.tasks import generate_report
            
            task = generate_report.delay(
                tenant_id=schedule.tenant_id,
                schedule_id=schedule.id,
                report_definition_id=schedule.report_definition_id,
                email_delivery_config=schedule.email_delivery_config,
            )
            
            logger.info(
                f"Enqueued report generation task {task.id} for schedule {schedule.id}",
                extra={
                    "schedule_id": schedule.id,
                    "task_id": task.id,
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to enqueue task for schedule {schedule.id}: {e}",
                exc_info=True,
                extra={"schedule_id": schedule.id},
            )
            # Don't raise - continue processing other schedules

        # Update schedule timestamps
        schedule.last_run_at = datetime.now(timezone.utc)

        # Calculate next run time
        try:
            schedule.next_run_at = calculate_next_run(
                cron_expr=schedule.cron_expression,
                tz=schedule.timezone,
            )
        except ValueError as e:
            logger.error(
                f"Failed to calculate next run for schedule {schedule.id}: {e}",
                extra={"schedule_id": schedule.id},
            )
            # Disable schedule if cron calculation fails
            schedule.is_active = False

        # Persist changes (will be committed by caller)
        session.add(schedule)


# Singleton instance
_scheduler_loop: Optional[SchedulerLoop] = None


async def get_scheduler_loop() -> SchedulerLoop:
    """Get or create the singleton scheduler loop instance."""
    global _scheduler_loop
    if _scheduler_loop is None:
        _scheduler_loop = SchedulerLoop(
            database_url=settings.DATABASE_URL,
            redis_url=settings.REDIS_URL,
        )
    return _scheduler_loop


async def start_scheduler_loop() -> None:
    """Start the scheduler loop (called on application startup)."""
    loop = await get_scheduler_loop()
    await loop.start()


async def stop_scheduler_loop() -> None:
    """Stop the scheduler loop (called on application shutdown)."""
    loop = await get_scheduler_loop()
    await loop.stop()
