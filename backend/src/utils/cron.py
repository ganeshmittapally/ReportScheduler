"""Cron expression validation and calculation utilities."""

from datetime import datetime, timezone
from typing import Optional

from croniter import croniter
import pytz


def validate_cron_expression(cron_expr: str) -> tuple[bool, Optional[str]]:
    """Validate a cron expression format.
    
    Args:
        cron_expr: The cron expression to validate (e.g., "0 9 * * *")
        
    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    """
    try:
        croniter(cron_expr)
        return True, None
    except (ValueError, KeyError) as e:
        return False, f"Invalid cron expression: {str(e)}"


def calculate_next_run(
    cron_expr: str,
    tz: str = "UTC",
    base_time: Optional[datetime] = None,
) -> datetime:
    """Calculate the next run time for a cron expression.
    
    Args:
        cron_expr: The cron expression (e.g., "0 9 * * *")
        tz: The timezone string (e.g., "America/New_York")
        base_time: The reference time (defaults to now in the specified timezone)
        
    Returns:
        The next run datetime in UTC with timezone info
        
    Raises:
        ValueError: If cron expression or timezone is invalid
    """
    try:
        timezone_obj = pytz.timezone(tz)
    except pytz.exceptions.UnknownTimeZoneError as e:
        raise ValueError(f"Invalid timezone: {tz}") from e

    if base_time is None:
        base_time = datetime.now(timezone_obj)
    elif base_time.tzinfo is None:
        # Localize naive datetime to the specified timezone
        base_time = timezone_obj.localize(base_time)
    else:
        # Convert to the specified timezone
        base_time = base_time.astimezone(timezone_obj)

    cron = croniter(cron_expr, base_time)
    next_run = cron.get_next(datetime)

    # Convert to UTC
    return next_run.astimezone(timezone.utc)


def get_next_n_runs(
    cron_expr: str,
    n: int = 5,
    tz: str = "UTC",
    base_time: Optional[datetime] = None,
) -> list[datetime]:
    """Get the next N run times for a cron expression.
    
    Useful for showing schedule preview to users.
    
    Args:
        cron_expr: The cron expression (e.g., "0 9 * * *")
        n: Number of future runs to calculate (default: 5, max: 20)
        tz: The timezone string (e.g., "America/New_York")
        base_time: The reference time (defaults to now in the specified timezone)
        
    Returns:
        List of next N run datetimes in UTC with timezone info
        
    Raises:
        ValueError: If cron expression or timezone is invalid
    """
    n = min(n, 20)  # Cap at 20 to prevent abuse

    try:
        timezone_obj = pytz.timezone(tz)
    except pytz.exceptions.UnknownTimeZoneError as e:
        raise ValueError(f"Invalid timezone: {tz}") from e

    if base_time is None:
        base_time = datetime.now(timezone_obj)
    elif base_time.tzinfo is None:
        base_time = timezone_obj.localize(base_time)
    else:
        base_time = base_time.astimezone(timezone_obj)

    cron = croniter(cron_expr, base_time)
    runs = []
    for _ in range(n):
        next_run = cron.get_next(datetime)
        runs.append(next_run.astimezone(timezone.utc))

    return runs


def get_human_readable_cron(cron_expr: str) -> str:
    """Convert cron expression to human-readable description.
    
    Args:
        cron_expr: The cron expression (e.g., "0 9 * * *")
        
    Returns:
        Human-readable description (e.g., "At 09:00 AM")
        
    Raises:
        ValueError: If cron expression is invalid
    """
    from cronstrue import get_description

    try:
        return get_description(cron_expr)
    except Exception as e:
        raise ValueError(f"Invalid cron expression: {str(e)}") from e
