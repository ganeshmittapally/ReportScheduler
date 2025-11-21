"""Pydantic schemas for schedule API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EmailDeliveryConfig(BaseModel):
    """Email delivery configuration schema."""

    recipients: list[str] = Field(..., min_length=1, max_length=50)
    subject: Optional[str] = Field(None, max_length=200)
    cc: Optional[list[str]] = Field(None, max_length=20)
    bcc: Optional[list[str]] = Field(None, max_length=20)

    @field_validator("recipients", "cc", "bcc")
    @classmethod
    def validate_emails(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate email addresses."""
        if v is None:
            return v
        for email in v:
            if "@" not in email or len(email) < 5:
                raise ValueError(f"Invalid email address: {email}")
        return v


class CreateScheduleRequest(BaseModel):
    """Request schema for creating a schedule."""

    report_definition_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    cron_expression: str = Field(..., min_length=5, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    email_delivery_config: Optional[EmailDeliveryConfig] = None


class UpdateScheduleRequest(BaseModel):
    """Request schema for updating a schedule."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cron_expression: Optional[str] = Field(None, min_length=5, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    email_delivery_config: Optional[EmailDeliveryConfig] = None


class ScheduleResponse(BaseModel):
    """Response schema for schedule data."""

    id: str
    tenant_id: str
    report_definition_id: str
    name: str
    cron_expression: str
    timezone: str
    is_active: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    email_delivery_config: Optional[dict]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ScheduleListResponse(BaseModel):
    """Response schema for paginated schedule list."""

    items: list[ScheduleResponse]
    next_cursor: Optional[str] = None
    total_count: Optional[int] = None


class CronPreviewRequest(BaseModel):
    """Request schema for cron expression preview."""

    cron_expression: str = Field(..., min_length=5, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    count: int = Field(default=5, ge=1, le=20)


class CronPreviewResponse(BaseModel):
    """Response schema for cron preview."""

    cron_expression: str
    description: str
    next_runs: list[datetime]
