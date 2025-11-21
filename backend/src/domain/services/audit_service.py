"""Audit and compliance tracking service."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Artifact, AuditEvent

logger = logging.getLogger(__name__)


class AuditService:
    """Service for tracking audit events and compliance reporting."""
    
    @staticmethod
    async def track_report_view(
        session: AsyncSession,
        tenant_id: str,
        artifact_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        """Track when a report is viewed (signed URL accessed).
        
        Args:
            session: Database session
            tenant_id: The tenant ID
            artifact_id: The artifact being viewed
            user_id: Optional user ID who viewed the report
            ip_address: Optional IP address of viewer
            user_agent: Optional user agent string
            
        Returns:
            Created AuditEvent record
        """
        event = AuditEvent(
            id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}",
            tenant_id=tenant_id,
            event_type="report_viewed",
            event_metadata={
                "artifact_id": artifact_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
            created_at=datetime.now(timezone.utc),
        )
        
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        logger.info(
            f"Tracked report view for artifact {artifact_id}",
            extra={
                "tenant_id": tenant_id,
                "artifact_id": artifact_id,
                "user_id": user_id,
            },
        )
        
        return event
    
    @staticmethod
    async def track_report_download(
        session: AsyncSession,
        tenant_id: str,
        artifact_id: str,
        user_id: Optional[str] = None,
        download_method: str = "direct_link",
    ) -> AuditEvent:
        """Track when a report is downloaded.
        
        Args:
            session: Database session
            tenant_id: The tenant ID
            artifact_id: The artifact being downloaded
            user_id: Optional user ID who downloaded
            download_method: How the report was downloaded
            
        Returns:
            Created AuditEvent record
        """
        event = AuditEvent(
            id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}",
            tenant_id=tenant_id,
            event_type="report_downloaded",
            event_metadata={
                "artifact_id": artifact_id,
                "user_id": user_id,
                "download_method": download_method,
            },
            created_at=datetime.now(timezone.utc),
        )
        
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        logger.info(
            f"Tracked report download for artifact {artifact_id}",
            extra={
                "tenant_id": tenant_id,
                "artifact_id": artifact_id,
                "user_id": user_id,
            },
        )
        
        return event
    
    @staticmethod
    async def track_report_shared(
        session: AsyncSession,
        tenant_id: str,
        artifact_id: str,
        shared_by_user_id: str,
        shared_with: list[str],
        share_method: str = "email",
    ) -> AuditEvent:
        """Track when a report is shared.
        
        Args:
            session: Database session
            tenant_id: The tenant ID
            artifact_id: The artifact being shared
            shared_by_user_id: User ID who shared the report
            shared_with: List of recipients (emails or user IDs)
            share_method: How the report was shared
            
        Returns:
            Created AuditEvent record
        """
        event = AuditEvent(
            id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}",
            tenant_id=tenant_id,
            event_type="report_shared",
            event_metadata={
                "artifact_id": artifact_id,
                "shared_by_user_id": shared_by_user_id,
                "shared_with": shared_with,
                "share_method": share_method,
                "recipient_count": len(shared_with),
            },
            created_at=datetime.now(timezone.utc),
        )
        
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        logger.info(
            f"Tracked report share for artifact {artifact_id}",
            extra={
                "tenant_id": tenant_id,
                "artifact_id": artifact_id,
                "recipient_count": len(shared_with),
            },
        )
        
        return event
    
    @staticmethod
    async def get_artifact_audit_trail(
        session: AsyncSession,
        artifact_id: str,
        tenant_id: str,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get audit trail for a specific artifact.
        
        Args:
            session: Database session
            artifact_id: The artifact ID
            tenant_id: The tenant ID
            limit: Max number of events to return
            
        Returns:
            List of AuditEvent records
        """
        query = (
            select(AuditEvent)
            .where(
                AuditEvent.tenant_id == tenant_id,
                AuditEvent.event_metadata["artifact_id"].astext == artifact_id,
            )
            .order_by(desc(AuditEvent.created_at))
            .limit(limit)
        )
        
        result = await session.execute(query)
        events = result.scalars().all()
        
        return list(events)
    
    @staticmethod
    async def get_user_activity(
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        event_types: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get audit events for a specific user.
        
        Args:
            session: Database session
            tenant_id: The tenant ID
            user_id: The user ID
            event_types: Optional filter by event types
            limit: Max number of events to return
            
        Returns:
            List of AuditEvent records
        """
        query = select(AuditEvent).where(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.event_metadata["user_id"].astext == user_id,
        )
        
        if event_types:
            query = query.where(AuditEvent.event_type.in_(event_types))
        
        query = query.order_by(desc(AuditEvent.created_at)).limit(limit)
        
        result = await session.execute(query)
        events = result.scalars().all()
        
        return list(events)
    
    @staticmethod
    async def generate_compliance_report(
        session: AsyncSession,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Generate compliance report for a date range.
        
        Args:
            session: Database session
            tenant_id: The tenant ID
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dict with compliance metrics
        """
        query = select(AuditEvent).where(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.created_at >= start_date,
            AuditEvent.created_at <= end_date,
        )
        
        result = await session.execute(query)
        events = result.scalars().all()
        
        # Aggregate metrics
        event_counts = {}
        unique_users = set()
        unique_artifacts = set()
        
        for event in events:
            # Count by event type
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Track unique users
            user_id = event.event_metadata.get("user_id")
            if user_id:
                unique_users.add(user_id)
            
            # Track unique artifacts
            artifact_id = event.event_metadata.get("artifact_id")
            if artifact_id:
                unique_artifacts.add(artifact_id)
        
        return {
            "tenant_id": tenant_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_events": len(events),
            "event_counts": event_counts,
            "unique_users": len(unique_users),
            "unique_artifacts": len(unique_artifacts),
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "created_at": e.created_at.isoformat(),
                    "metadata": e.event_metadata,
                }
                for e in events
            ],
        }


class ArtifactRetentionService:
    """Service for managing artifact retention and cleanup."""
    
    @staticmethod
    async def find_expired_artifacts(
        session: AsyncSession,
        tenant_id: Optional[str] = None,
        retention_days: int = 90,
    ) -> list[Artifact]:
        """Find artifacts that have exceeded retention period.
        
        Args:
            session: Database session
            tenant_id: Optional tenant ID to filter by
            retention_days: Number of days to retain artifacts
            
        Returns:
            List of expired Artifact records
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        query = select(Artifact).where(Artifact.created_at < cutoff_date)
        
        if tenant_id:
            query = query.where(Artifact.tenant_id == tenant_id)
        
        result = await session.execute(query)
        artifacts = result.scalars().all()
        
        logger.info(
            f"Found {len(artifacts)} expired artifacts (retention: {retention_days} days)",
            extra={"tenant_id": tenant_id, "count": len(artifacts)},
        )
        
        return list(artifacts)
    
    @staticmethod
    async def delete_expired_artifacts(
        session: AsyncSession,
        blob_storage_service,
        tenant_id: Optional[str] = None,
        retention_days: int = 90,
        dry_run: bool = False,
    ) -> dict:
        """Delete expired artifacts from database and blob storage.
        
        Args:
            session: Database session
            blob_storage_service: BlobStorageService instance
            tenant_id: Optional tenant ID to filter by
            retention_days: Number of days to retain artifacts
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dict with deletion results
        """
        from datetime import timedelta
        
        expired_artifacts = await ArtifactRetentionService.find_expired_artifacts(
            session, tenant_id, retention_days
        )
        
        deleted_count = 0
        failed_count = 0
        total_size_bytes = 0
        
        for artifact in expired_artifacts:
            total_size_bytes += artifact.file_size_bytes
            
            if dry_run:
                logger.info(
                    f"[DRY RUN] Would delete artifact {artifact.id} ({artifact.blob_path})"
                )
                deleted_count += 1
                continue
            
            try:
                # Delete from blob storage
                blob_storage_service.delete_artifact(artifact.blob_path)
                
                # Delete from database
                await session.delete(artifact)
                
                deleted_count += 1
                
                logger.info(
                    f"Deleted expired artifact {artifact.id}",
                    extra={
                        "artifact_id": artifact.id,
                        "blob_path": artifact.blob_path,
                        "size_bytes": artifact.file_size_bytes,
                    },
                )
                
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Failed to delete artifact {artifact.id}: {e}",
                    exc_info=True,
                )
        
        if not dry_run:
            await session.commit()
        
        return {
            "total_expired": len(expired_artifacts),
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / 1024 / 1024, 2),
            "dry_run": dry_run,
        }
