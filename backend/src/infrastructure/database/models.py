"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Integer, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Tenant(Base):
    """Tenant model for multi-tenancy."""

    __tablename__ = "tenant"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="standard"
    )  # standard, premium, enterprise
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    report_definitions: Mapped[list["ReportDefinition"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"


class ReportDefinition(Base):
    """Report definition model."""

    __tablename__ = "report_definition"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    query_spec: Mapped[dict] = mapped_column(JSON, nullable=False)  # data source, query, params
    template_ref: Mapped[str] = mapped_column(String(500), nullable=False)  # Blob storage path
    output_format: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pdf"
    )  # pdf, csv, xlsx
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="report_definitions")
    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="report_definition", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (Index("idx_report_tenant_id", "tenant_id"),)

    def __repr__(self) -> str:
        return f"<ReportDefinition(id={self.id}, name={self.name})>"


class Schedule(Base):
    """Schedule model for recurring reports."""

    __tablename__ = "schedule"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=False)
    report_definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("report_definition.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_delivery_config: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # recipients, subject, body_template
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="schedules")
    report_definition: Mapped["ReportDefinition"] = relationship(back_populates="schedules")
    execution_runs: Mapped[list["ExecutionRun"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_schedule_tenant_id", "tenant_id"),
        Index("idx_schedule_next_run", "next_run_at", "is_active"),
        Index("idx_schedule_report_id", "report_definition_id"),
    )

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, name={self.name}, cron={self.cron_expression})>"


class ExecutionRun(Base):
    """Execution run model for tracking report generation."""

    __tablename__ = "execution_run"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=False)
    schedule_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schedule.id"), nullable=True
    )  # Nullable for manual runs
    report_definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("report_definition.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, running, completed, failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Additional context
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship()
    schedule: Mapped[Optional["Schedule"]] = relationship(back_populates="execution_runs")
    report_definition: Mapped["ReportDefinition"] = relationship()
    artifact: Mapped[Optional["Artifact"]] = relationship(back_populates="execution_run")

    # Indexes
    __table_args__ = (
        Index("idx_execution_tenant_id", "tenant_id"),
        Index("idx_execution_schedule_id", "schedule_id"),
        Index("idx_execution_status", "status"),
        Index("idx_execution_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ExecutionRun(id={self.id}, status={self.status})>"


class Artifact(Base):
    """Artifact model for generated report files."""

    __tablename__ = "artifact"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=False)
    execution_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("execution_run.id"), nullable=False, unique=True
    )
    blob_path: Mapped[str] = mapped_column(String(1000), nullable=False)  # Azure Blob Storage path
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, csv, xlsx
    signed_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # SAS URL (7-day expiry)
    signed_url_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship()
    execution_run: Mapped["ExecutionRun"] = relationship(back_populates="artifact")

    # Indexes
    __table_args__ = (
        Index("idx_artifact_tenant_id", "tenant_id"),
        Index("idx_artifact_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, format={self.file_format})>"


class DeliveryReceipt(Base):
    """Delivery receipt model for email/webhook delivery tracking."""

    __tablename__ = "delivery_receipt"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=False)
    artifact_id: Mapped[str] = mapped_column(String(36), ForeignKey("artifact.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # email, webhook, slack
    recipient: Mapped[str] = mapped_column(String(500), nullable=False)  # email address or URL
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, sent, failed, bounced
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship()
    artifact: Mapped["Artifact"] = relationship()

    # Indexes
    __table_args__ = (
        Index("idx_delivery_tenant_id", "tenant_id"),
        Index("idx_delivery_artifact_id", "artifact_id"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryReceipt(id={self.id}, channel={self.channel}, status={self.status})>"


class AuditEvent(Base):
    """Audit event model for compliance and tracking."""

    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # create_report, delete_schedule, etc.
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)  # report, schedule, etc.
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship()

    # Indexes
    __table_args__ = (
        Index("idx_audit_tenant_id", "tenant_id"),
        Index("idx_audit_created_at", "created_at"),
        Index("idx_audit_event_type", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, event_type={self.event_type})>"
