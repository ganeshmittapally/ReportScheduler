"""Advanced scheduling utilities for date ranges and incremental reports."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class DateRangeCalculator:
    """Calculate date ranges for scheduled reports."""
    
    @staticmethod
    def calculate_range(
        range_type: str,
        reference_date: Optional[datetime] = None,
        timezone_str: str = "UTC",
    ) -> dict:
        """Calculate date range based on range type.
        
        Args:
            range_type: Type of date range (e.g., "last_7_days", "last_30_days", 
                       "last_month", "month_to_date", "year_to_date", "custom")
            reference_date: Reference date for calculations (default: now)
            timezone_str: Timezone for date calculations
            
        Returns:
            Dict with start_date and end_date
        """
        if reference_date is None:
            reference_date = datetime.now(timezone.utc)
        
        # Ensure datetime is timezone-aware
        if reference_date.tzinfo is None:
            reference_date = reference_date.replace(tzinfo=timezone.utc)
        
        if range_type == "last_7_days":
            start_date = reference_date - timedelta(days=7)
            end_date = reference_date
            
        elif range_type == "last_30_days":
            start_date = reference_date - timedelta(days=30)
            end_date = reference_date
            
        elif range_type == "last_90_days":
            start_date = reference_date - timedelta(days=90)
            end_date = reference_date
            
        elif range_type == "yesterday":
            start_date = (reference_date - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_date = start_date.replace(hour=23, minute=59, second=59)
            
        elif range_type == "last_week":
            # Previous Monday to Sunday
            days_since_monday = reference_date.weekday()
            last_monday = reference_date - timedelta(days=days_since_monday + 7)
            start_date = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=6)).replace(
                hour=23, minute=59, second=59
            )
            
        elif range_type == "last_month":
            # Previous calendar month
            first_of_this_month = reference_date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end_date = first_of_this_month - timedelta(microseconds=1)
            start_date = end_date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            
        elif range_type == "month_to_date":
            # First day of current month to now
            start_date = reference_date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end_date = reference_date
            
        elif range_type == "quarter_to_date":
            # First day of current quarter to now
            current_quarter = (reference_date.month - 1) // 3
            first_month_of_quarter = current_quarter * 3 + 1
            start_date = reference_date.replace(
                month=first_month_of_quarter,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            end_date = reference_date
            
        elif range_type == "year_to_date":
            # First day of current year to now
            start_date = reference_date.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end_date = reference_date
            
        elif range_type == "last_year":
            # Previous calendar year
            start_date = reference_date.replace(
                year=reference_date.year - 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            end_date = reference_date.replace(
                year=reference_date.year - 1,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
            )
            
        elif range_type == "last_hour":
            start_date = reference_date - timedelta(hours=1)
            end_date = reference_date
            
        elif range_type == "last_24_hours":
            start_date = reference_date - timedelta(hours=24)
            end_date = reference_date
            
        else:
            # Default to last 7 days
            logger.warning(
                f"Unknown range_type '{range_type}', defaulting to last_7_days"
            )
            start_date = reference_date - timedelta(days=7)
            end_date = reference_date
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "range_type": range_type,
            "reference_date": reference_date.isoformat(),
        }


class IncrementalReportTracker:
    """Track state for incremental reports."""
    
    @staticmethod
    def get_incremental_range(
        last_execution_completed_at: Optional[datetime],
        current_time: Optional[datetime] = None,
        overlap_seconds: int = 60,
    ) -> dict:
        """Calculate date range for incremental report.
        
        Args:
            last_execution_completed_at: When the last execution completed
            current_time: Current execution time (default: now)
            overlap_seconds: Seconds to overlap with previous run to avoid gaps
            
        Returns:
            Dict with start_date and end_date for incremental query
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        if last_execution_completed_at is None:
            # First run - use default range (e.g., last 7 days)
            start_date = current_time - timedelta(days=7)
            is_first_run = True
        else:
            # Incremental run - start from last run with overlap
            start_date = last_execution_completed_at - timedelta(seconds=overlap_seconds)
            is_first_run = False
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": current_time.isoformat(),
            "is_incremental": not is_first_run,
            "is_first_run": is_first_run,
            "overlap_seconds": overlap_seconds,
        }
