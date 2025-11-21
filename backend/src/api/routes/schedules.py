"""Schedule API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.schedule import (
    CreateScheduleRequest,
    CronPreviewRequest,
    CronPreviewResponse,
    ScheduleListResponse,
    ScheduleResponse,
    UpdateScheduleRequest,
)
from src.domain.services.schedule_service import ScheduleService
from src.infrastructure.database.repositories.postgres_schedule_repository import (
    PostgresScheduleRepository,
)
from src.infrastructure.database.session import get_db
from src.utils.cron import get_human_readable_cron, get_next_n_runs

router = APIRouter(prefix="/v1/schedules", tags=["schedules"])


# Dependency to get service (in real app, this would use proper DI)
def get_schedule_service(
    db: AsyncSession = Depends(get_db),
) -> ScheduleService:
    """Get schedule service with dependencies."""
    repository = PostgresScheduleRepository(db)
    return ScheduleService(repository)


# Mock function to get current tenant context (replace with real auth)
async def get_current_tenant() -> tuple[str, str, str]:
    """Get current tenant from auth context.
    
    In production, this would extract tenant info from JWT token.
    
    Returns:
        Tuple of (tenant_id, tenant_tier, user_id)
    """
    # TODO: Replace with real authentication
    return "tenant-123", "premium", "user-456"


@router.post(
    "",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new schedule",
)
async def create_schedule(
    request: CreateScheduleRequest,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_context: tuple[str, str, str] = Depends(get_current_tenant),
) -> ScheduleResponse:
    """Create a new schedule for a report.
    
    Args:
        request: The schedule creation request
        service: The schedule service (injected)
        tenant_context: Current tenant context (injected)
        
    Returns:
        The created schedule
        
    Raises:
        HTTPException: If validation fails or quota exceeded
    """
    tenant_id, tenant_tier, user_id = tenant_context

    schedule, error = await service.create_schedule(
        tenant_id=tenant_id,
        tenant_tier=tenant_tier,
        report_definition_id=request.report_definition_id,
        name=request.name,
        cron_expression=request.cron_expression,
        timezone=request.timezone,
        email_delivery_config=(
            request.email_delivery_config.model_dump()
            if request.email_delivery_config
            else None
        ),
        created_by=user_id,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ScheduleResponse.model_validate(schedule)


@router.get(
    "",
    response_model=ScheduleListResponse,
    summary="List schedules",
)
async def list_schedules(
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: ScheduleService = Depends(get_schedule_service),
    tenant_context: tuple[str, str, str] = Depends(get_current_tenant),
) -> ScheduleListResponse:
    """List schedules for the current tenant with pagination.
    
    Args:
        cursor: Opaque cursor for pagination
        limit: Maximum number of items to return (1-100)
        is_active: Filter by active status (None = all)
        service: The schedule service (injected)
        tenant_context: Current tenant context (injected)
        
    Returns:
        Paginated list of schedules
    """
    tenant_id, _, _ = tenant_context

    schedules, next_cursor = await service.list_schedules(
        tenant_id=tenant_id,
        cursor=cursor,
        limit=limit,
        is_active=is_active,
    )

    return ScheduleListResponse(
        items=[ScheduleResponse.model_validate(s) for s in schedules],
        next_cursor=next_cursor,
    )


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Get a schedule by ID",
)
async def get_schedule(
    schedule_id: str,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_context: tuple[str, str, str] = Depends(get_current_tenant),
) -> ScheduleResponse:
    """Get a single schedule by ID.
    
    Args:
        schedule_id: The schedule unique identifier
        service: The schedule service (injected)
        tenant_context: Current tenant context (injected)
        
    Returns:
        The schedule
        
    Raises:
        HTTPException: If schedule not found
    """
    tenant_id, _, _ = tenant_context

    schedule = await service.get_schedule(
        schedule_id=schedule_id,
        tenant_id=tenant_id,
    )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    return ScheduleResponse.model_validate(schedule)


@router.put(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Update a schedule",
)
async def update_schedule(
    schedule_id: str,
    request: UpdateScheduleRequest,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_context: tuple[str, str, str] = Depends(get_current_tenant),
) -> ScheduleResponse:
    """Update an existing schedule.
    
    Args:
        schedule_id: The schedule unique identifier
        request: The schedule update request
        service: The schedule service (injected)
        tenant_context: Current tenant context (injected)
        
    Returns:
        The updated schedule
        
    Raises:
        HTTPException: If schedule not found or validation fails
    """
    tenant_id, _, _ = tenant_context

    schedule, error = await service.update_schedule(
        schedule_id=schedule_id,
        tenant_id=tenant_id,
        name=request.name,
        cron_expression=request.cron_expression,
        timezone=request.timezone,
        email_delivery_config=(
            request.email_delivery_config.model_dump()
            if request.email_delivery_config
            else None
        ),
    )

    if error:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if error == "Schedule not found"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=error)

    return ScheduleResponse.model_validate(schedule)


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a schedule",
)
async def delete_schedule(
    schedule_id: str,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_context: tuple[str, str, str] = Depends(get_current_tenant),
) -> None:
    """Delete a schedule.
    
    Args:
        schedule_id: The schedule unique identifier
        service: The schedule service (injected)
        tenant_context: Current tenant context (injected)
        
    Raises:
        HTTPException: If schedule not found
    """
    tenant_id, _, _ = tenant_context

    deleted = await service.delete_schedule(
        schedule_id=schedule_id,
        tenant_id=tenant_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )


@router.patch(
    "/{schedule_id}/pause",
    response_model=ScheduleResponse,
    summary="Pause a schedule",
)
async def pause_schedule(
    schedule_id: str,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_context: tuple[str, str, str] = Depends(get_current_tenant),
) -> ScheduleResponse:
    """Pause a schedule (set is_active to False).
    
    Args:
        schedule_id: The schedule unique identifier
        service: The schedule service (injected)
        tenant_context: Current tenant context (injected)
        
    Returns:
        The updated schedule
        
    Raises:
        HTTPException: If schedule not found
    """
    tenant_id, _, _ = tenant_context

    schedule, error = await service.pause_schedule(
        schedule_id=schedule_id,
        tenant_id=tenant_id,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error,
        )

    return ScheduleResponse.model_validate(schedule)


@router.patch(
    "/{schedule_id}/resume",
    response_model=ScheduleResponse,
    summary="Resume a schedule",
)
async def resume_schedule(
    schedule_id: str,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_context: tuple[str, str, str] = Depends(get_current_tenant),
) -> ScheduleResponse:
    """Resume a paused schedule (set is_active to True).
    
    Args:
        schedule_id: The schedule unique identifier
        service: The schedule service (injected)
        tenant_context: Current tenant context (injected)
        
    Returns:
        The updated schedule
        
    Raises:
        HTTPException: If schedule not found or validation fails
    """
    tenant_id, _, _ = tenant_context

    schedule, error = await service.resume_schedule(
        schedule_id=schedule_id,
        tenant_id=tenant_id,
    )

    if error:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if error == "Schedule not found"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=error)

    return ScheduleResponse.model_validate(schedule)


@router.post(
    "/cron/preview",
    response_model=CronPreviewResponse,
    summary="Preview cron expression",
)
async def preview_cron(
    request: CronPreviewRequest,
) -> CronPreviewResponse:
    """Preview a cron expression with next N run times.
    
    Useful for showing users when their schedule will run.
    
    Args:
        request: The cron preview request
        
    Returns:
        Cron description and next run times
        
    Raises:
        HTTPException: If cron expression or timezone is invalid
    """
    try:
        description = get_human_readable_cron(request.cron_expression)
        next_runs = get_next_n_runs(
            cron_expr=request.cron_expression,
            n=request.count,
            tz=request.timezone,
        )

        return CronPreviewResponse(
            cron_expression=request.cron_expression,
            description=description,
            next_runs=next_runs,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
