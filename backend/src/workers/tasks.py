"""Celery tasks for report generation and delivery."""

import io
import logging
from datetime import datetime, timezone
from typing import Optional

from celery import Task
from liquidpy import Liquid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from weasyprint import HTML

from src.config import settings
from src.infrastructure.azure.blob_storage import BlobStorageService
from src.infrastructure.cache.report_cache import ReportCacheService
from src.infrastructure.database.models import (
    Artifact,
    AuditEvent,
    DeliveryReceipt,
    ExecutionRun,
    ReportDefinition,
    Schedule,
)
from src.infrastructure.email.email_service import EmailService
from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""
    
    _engine = None
    _session_maker = None
    
    @property
    def engine(self):
        """Get or create database engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_size=5,
                max_overflow=10,
            )
        return self._engine
    
    @property
    def session_maker(self):
        """Get or create session maker."""
        if self._session_maker is None:
            self._session_maker = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_maker


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="src.workers.tasks.generate_report",
    max_retries=3,
    default_retry_delay=60,
)
def generate_report(
    self,
    tenant_id: str,
    schedule_id: Optional[str],
    report_definition_id: str,
    email_delivery_config: Optional[dict] = None,
) -> dict:
    """Generate a report and optionally deliver via email.
    
    This is the main Celery task that orchestrates report generation:
    1. Create ExecutionRun record
    2. Fetch data from source (Synapse)
    3. Render template with data
    4. Generate PDF
    5. Upload to Blob Storage
    6. Create Artifact record
    7. Send email (if configured)
    8. Create DeliveryReceipt record
    
    Args:
        tenant_id: The tenant unique identifier
        schedule_id: The schedule ID (None for manual runs)
        report_definition_id: The report definition to generate
        email_delivery_config: Optional email configuration
        
    Returns:
        Dict with execution details
    """
    import asyncio
    
    # Run async task in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _generate_report_async(
                task=self,
                tenant_id=tenant_id,
                schedule_id=schedule_id,
                report_definition_id=report_definition_id,
                email_delivery_config=email_delivery_config,
            )
        )
        return result
    finally:
        loop.close()


async def _generate_report_async(
    task: DatabaseTask,
    tenant_id: str,
    schedule_id: Optional[str],
    report_definition_id: str,
    email_delivery_config: Optional[dict],
) -> dict:
    """Async implementation of report generation.
    
    Args:
        task: The Celery task instance
        tenant_id: The tenant unique identifier
        schedule_id: The schedule ID (None for manual runs)
        report_definition_id: The report definition to generate
        email_delivery_config: Optional email configuration
        
    Returns:
        Dict with execution details
    """
    execution_run_id = None
    started_at = datetime.now(timezone.utc)
    
    async with task.session_maker() as session:
        try:
            # 0. Increment burst protection counter
            from src.domain.services.burst_protection import BurstProtectionService
            
            burst_protection = BurstProtectionService()
            await burst_protection.increment_execution_count(tenant_id)
            
            # 1. Create ExecutionRun record
            execution_run = ExecutionRun(
                id=f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{tenant_id[:8]}",
                tenant_id=tenant_id,
                schedule_id=schedule_id,
                report_definition_id=report_definition_id,
                status="running",
                started_at=started_at,
                execution_metadata={"task_id": task.request.id},
                created_at=started_at,
            )
            session.add(execution_run)
            await session.commit()
            await session.refresh(execution_run)
            execution_run_id = execution_run.id
            
            logger.info(
                f"Started report generation: {execution_run_id}",
                extra={
                    "execution_run_id": execution_run_id,
                    "tenant_id": tenant_id,
                    "report_definition_id": report_definition_id,
                },
            )
            
            # 2. Fetch report definition
            report_def = await session.get(ReportDefinition, report_definition_id)
            if not report_def:
                raise ValueError(f"Report definition not found: {report_definition_id}")
            
            # 2.5. Check cache if report is cacheable
            pdf_bytes = None
            cache_hit = False
            cache_ttl = report_def.execution_metadata.get("cache_ttl_seconds") if report_def.execution_metadata else None
            
            if cache_ttl and cache_ttl > 0:
                cache_service = ReportCacheService()
                cached = await cache_service.get_cached_report(
                    report_definition_id=report_definition_id,
                    query_parameters=report_def.query_spec,
                    date_range=None,  # TODO: Extract from schedule or execution context
                )
                
                if cached:
                    pdf_bytes = cached["pdf_bytes"]
                    cache_hit = True
                    execution_run.execution_metadata["cache_hit"] = True
                    execution_run.execution_metadata["cached_at"] = cached["metadata"].get("cached_at")
                    logger.info(f"Using cached report for {execution_run_id}")
            
            # 3-5. Generate report if not cached
            if not cache_hit:
                # 3. Fetch data from source (mock implementation)
                # TODO: Replace with actual Synapse query execution
                report_data = await _fetch_report_data(report_def.query_spec)
                
                # 4. Render template with data
                rendered_html = await _render_template(
                    template_ref=report_def.template_ref,
                    data=report_data,
                    report_name=report_def.name,
                )
                
                # 5. Generate PDF
                pdf_bytes = await _generate_pdf(rendered_html)
                
                # 5.5. Cache the report if caching is enabled
                if cache_ttl and cache_ttl > 0:
                    cache_service = ReportCacheService()
                    await cache_service.cache_report(
                        report_definition_id=report_definition_id,
                        pdf_bytes=pdf_bytes,
                        query_parameters=report_def.query_spec,
                        date_range=None,
                        ttl_seconds=cache_ttl,
                        metadata={
                            "execution_run_id": execution_run_id,
                            "report_name": report_def.name,
                        },
                    )
            
            # 6. Upload to Blob Storage
            blob_service = BlobStorageService()
            blob_path, file_size_bytes = blob_service.upload_artifact(
                tenant_id=tenant_id,
                execution_run_id=execution_run_id,
                file_content=pdf_bytes,
                file_format=report_def.output_format,
            )
            
            # Generate SAS URL
            signed_url, signed_url_expires_at = blob_service.generate_sas_url(blob_path)
            
            # 7. Create Artifact record
            artifact = Artifact(
                id=f"artifact_{execution_run_id}",
                tenant_id=tenant_id,
                execution_run_id=execution_run_id,
                blob_path=blob_path,
                file_size_bytes=file_size_bytes,
                file_format=report_def.output_format,
                signed_url=signed_url,
                signed_url_expires_at=signed_url_expires_at,
                created_at=datetime.now(timezone.utc),
            )
            session.add(artifact)
            
            # 8. Send email if configured
            if email_delivery_config and email_delivery_config.get("recipients"):
                await _send_report_email(
                    session=session,
                    tenant_id=tenant_id,
                    artifact=artifact,
                    report_name=report_def.name,
                    email_config=email_delivery_config,
                    execution_time=started_at.isoformat(),
                )
            
            # 9. Update ExecutionRun to completed
            completed_at = datetime.now(timezone.utc)
            execution_run.status = "completed"
            execution_run.completed_at = completed_at
            execution_run.duration_seconds = int((completed_at - started_at).total_seconds())
            
            await session.commit()
            
            # Decrement burst protection counter
            await burst_protection.decrement_execution_count(tenant_id)
            
            logger.info(
                f"Completed report generation: {execution_run_id}",
                extra={
                    "execution_run_id": execution_run_id,
                    "duration_seconds": execution_run.duration_seconds,
                    "file_size_bytes": file_size_bytes,
                },
            )
            
            return {
                "execution_run_id": execution_run_id,
                "status": "completed",
                "artifact_id": artifact.id,
                "blob_path": blob_path,
                "file_size_bytes": file_size_bytes,
                "duration_seconds": execution_run.duration_seconds,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to generate report: {e}",
                exc_info=True,
                extra={
                    "execution_run_id": execution_run_id,
                    "tenant_id": tenant_id,
                    "report_definition_id": report_definition_id,
                },
            )
            
            # Decrement burst protection counter on failure
            try:
                from src.domain.services.burst_protection import BurstProtectionService
                burst_protection = BurstProtectionService()
                await burst_protection.decrement_execution_count(tenant_id)
            except Exception as burst_error:
                logger.error(f"Failed to decrement burst protection counter: {burst_error}")
            
            # Update ExecutionRun to failed
            if execution_run_id:
                try:
                    execution_run = await session.get(ExecutionRun, execution_run_id)
                    if execution_run:
                        execution_run.status = "failed"
                        execution_run.completed_at = datetime.now(timezone.utc)
                        execution_run.duration_seconds = int(
                            (execution_run.completed_at - started_at).total_seconds()
                        )
                        execution_run.error_message = str(e)[:1000]  # Limit error message length
                        await session.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update ExecutionRun status: {update_error}")
            
            # Retry task if retries remaining
            if task.request.retries < task.max_retries:
                raise task.retry(exc=e, countdown=60 * (task.request.retries + 1))
            
            return {
                "execution_run_id": execution_run_id,
                "status": "failed",
                "error": str(e),
            }


async def _fetch_report_data(query_spec: dict) -> dict:
    """Fetch data from data source (Synapse).
    
    Args:
        query_spec: Query specification with connection and query details
        
    Returns:
        Report data as dict
    """
    # TODO: Implement actual Synapse query execution
    # For now, return mock data
    logger.info("Fetching report data (mock implementation)")
    
    return {
        "title": "Sales Report",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": [
            {"product": "Product A", "quantity": 100, "revenue": 10000},
            {"product": "Product B", "quantity": 50, "revenue": 5000},
            {"product": "Product C", "quantity": 75, "revenue": 7500},
        ],
        "total_revenue": 22500,
        "total_quantity": 225,
    }


async def _render_template(template_ref: str, data: dict, report_name: str) -> str:
    """Render report template with data using Liquid.
    
    Args:
        template_ref: Reference to template (file path or content)
        data: Data to render in template
        report_name: Name of the report
        
    Returns:
        Rendered HTML content
    """
    logger.info(f"Rendering template: {template_ref}")
    
    # TODO: Fetch template from Blob Storage or use embedded template
    # For now, use a simple inline template
    template_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{{ title }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #1976D2; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #1976D2; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .footer { margin-top: 40px; color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Quantity</th>
                    <th>Revenue</th>
                </tr>
            </thead>
            <tbody>
                {% for row in rows %}
                <tr>
                    <td>{{ row.product }}</td>
                    <td>{{ row.quantity }}</td>
                    <td>${{ row.revenue }}</td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot>
                <tr>
                    <th>Total</th>
                    <th>{{ total_quantity }}</th>
                    <th>${{ total_revenue }}</th>
                </tr>
            </tfoot>
        </table>
        
        <div class="footer">
            <p>This report was automatically generated by Report Scheduler.</p>
        </div>
    </body>
    </html>
    """
    
    # Render template with Liquid
    liq = Liquid(template_content, liquid_loglevel="ERROR")
    rendered = liq.render(**data)
    
    return rendered


async def _generate_pdf(html_content: str) -> bytes:
    """Generate PDF from HTML using WeasyPrint.
    
    Args:
        html_content: HTML content to convert to PDF
        
    Returns:
        PDF content as bytes
    """
    logger.info("Generating PDF from HTML")
    
    # Convert HTML to PDF
    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_bytes = pdf_file.getvalue()
    
    logger.info(f"Generated PDF: {len(pdf_bytes)} bytes")
    return pdf_bytes


async def _send_report_email(
    session: AsyncSession,
    tenant_id: str,
    artifact: Artifact,
    report_name: str,
    email_config: dict,
    execution_time: str,
) -> None:
    """Send report delivery email.
    
    Args:
        session: Database session
        tenant_id: The tenant unique identifier
        artifact: The artifact record
        report_name: Name of the report
        email_config: Email configuration with recipients, subject, etc.
        execution_time: When the report was generated
    """
    logger.info("Sending report delivery email")
    
    email_service = EmailService()
    
    # Send email
    success, message_id_or_error = email_service.send_report_email(
        recipients=email_config["recipients"],
        subject=email_config.get("subject", f"Report: {report_name}"),
        artifact_url=artifact.signed_url,
        report_name=report_name,
        execution_time=execution_time,
        cc=email_config.get("cc"),
        bcc=email_config.get("bcc"),
    )
    
    # Create delivery receipt for each recipient
    for recipient in email_config["recipients"]:
        receipt = DeliveryReceipt(
            id=f"receipt_{artifact.id}_{recipient[:20]}",
            tenant_id=tenant_id,
            artifact_id=artifact.id,
            channel="email",
            recipient=recipient,
            status="sent" if success else "failed",
            sent_at=datetime.now(timezone.utc) if success else None,
            error_message=message_id_or_error if not success else None,
            created_at=datetime.now(timezone.utc),
        )
        session.add(receipt)
    
    logger.info(
        f"Email delivery {'successful' if success else 'failed'}",
        extra={
            "success": success,
            "recipients": email_config["recipients"],
            "message_id_or_error": message_id_or_error,
        },
    )


@celery_app.task(
    name="src.workers.tasks.send_email",
    max_retries=3,
    default_retry_delay=30,
)
def send_email(
    recipients: list[str],
    subject: str,
    html_content: str,
    plain_text: Optional[str] = None,
) -> dict:
    """Send a standalone email (for notifications, alerts, etc.).
    
    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        html_content: HTML email content
        plain_text: Optional plain text fallback
        
    Returns:
        Dict with send status
    """
    logger.info(f"Sending email to {len(recipients)} recipients")
    
    email_service = EmailService()
    
    # TODO: Implement generic email sending
    # For now, just log
    logger.info(f"Email task executed: {subject} -> {recipients}")
    
    return {
        "status": "sent",
        "recipients": recipients,
        "subject": subject,
    }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="src.workers.tasks.cleanup_expired_artifacts",
)
def cleanup_expired_artifacts(
    self,
    retention_days: int = 90,
    dry_run: bool = False,
) -> dict:
    """Cleanup expired artifacts from database and blob storage.
    
    This task should be scheduled to run daily (e.g., via Celery Beat).
    
    Args:
        retention_days: Number of days to retain artifacts (default: 90)
        dry_run: If True, only report what would be deleted
        
    Returns:
        Dict with cleanup results
    """
    import asyncio
    from src.domain.services.audit_service import ArtifactRetentionService
    from src.infrastructure.azure.blob_storage import BlobStorageService
    
    logger.info(
        f"Starting artifact cleanup (retention: {retention_days} days, dry_run: {dry_run})"
    )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _cleanup_expired_artifacts_async(
                task=self,
                retention_days=retention_days,
                dry_run=dry_run,
            )
        )
        return result
    finally:
        loop.close()


async def _cleanup_expired_artifacts_async(
    task: DatabaseTask,
    retention_days: int,
    dry_run: bool,
) -> dict:
    """Async implementation of artifact cleanup.
    
    Args:
        task: The Celery task instance
        retention_days: Number of days to retain artifacts
        dry_run: If True, only report what would be deleted
        
    Returns:
        Dict with cleanup results
    """
    async with task.session_maker() as session:
        try:
            blob_service = BlobStorageService()
            retention_service = ArtifactRetentionService()
            
            result = await retention_service.delete_expired_artifacts(
                session=session,
                blob_storage_service=blob_service,
                tenant_id=None,  # Cleanup for all tenants
                retention_days=retention_days,
                dry_run=dry_run,
            )
            
            logger.info(
                f"Artifact cleanup completed: {result['deleted_count']} deleted, "
                f"{result['failed_count']} failed, {result['total_size_mb']} MB freed"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup artifacts: {e}", exc_info=True)
            return {
                "total_expired": 0,
                "deleted_count": 0,
                "failed_count": 0,
                "error": str(e),
            }
