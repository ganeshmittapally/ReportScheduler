"""Azure Blob Storage service for artifact management."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

from src.config import settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Service for managing artifacts in Azure Blob Storage."""
    
    def __init__(self):
        """Initialize Blob Storage client."""
        self._client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self._container_name = settings.STORAGE_CONTAINER_NAME
        self._ensure_container_exists()
    
    def _ensure_container_exists(self) -> None:
        """Create container if it doesn't exist."""
        try:
            container_client = self._client.get_container_client(self._container_name)
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created blob container: {self._container_name}")
        except AzureError as e:
            logger.error(f"Failed to ensure container exists: {e}")
            raise
    
    def upload_artifact(
        self,
        tenant_id: str,
        execution_run_id: str,
        file_content: bytes,
        file_format: str,
        file_name: Optional[str] = None,
    ) -> tuple[str, int]:
        """Upload artifact to blob storage.
        
        Args:
            tenant_id: The tenant unique identifier
            execution_run_id: The execution run unique identifier
            file_content: The file content as bytes
            file_format: The file format (pdf, csv, xlsx)
            file_name: Optional custom file name (defaults to generated name)
            
        Returns:
            Tuple of (blob_path, file_size_bytes)
            
        Raises:
            AzureError: If upload fails
        """
        # Generate blob path: tenant_id/execution_run_id/filename.ext
        if file_name is None:
            file_name = f"report_{execution_run_id}.{file_format}"
        
        blob_path = f"{tenant_id}/{execution_run_id}/{file_name}"
        
        try:
            blob_client = self._client.get_blob_client(
                container=self._container_name,
                blob=blob_path,
            )
            
            # Upload with metadata
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                metadata={
                    "tenant_id": tenant_id,
                    "execution_run_id": execution_run_id,
                    "file_format": file_format,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            
            file_size_bytes = len(file_content)
            
            logger.info(
                f"Uploaded artifact to blob storage: {blob_path} ({file_size_bytes} bytes)",
                extra={
                    "tenant_id": tenant_id,
                    "execution_run_id": execution_run_id,
                    "blob_path": blob_path,
                    "file_size_bytes": file_size_bytes,
                },
            )
            
            return blob_path, file_size_bytes
            
        except AzureError as e:
            logger.error(
                f"Failed to upload artifact: {e}",
                exc_info=True,
                extra={
                    "tenant_id": tenant_id,
                    "execution_run_id": execution_run_id,
                    "blob_path": blob_path,
                },
            )
            raise
    
    def generate_sas_url(
        self,
        blob_path: str,
        expiry_hours: int = 24,
    ) -> tuple[str, datetime]:
        """Generate a SAS URL for accessing a blob.
        
        Args:
            blob_path: The blob path in the container
            expiry_hours: Hours until the SAS URL expires (default: 24)
            
        Returns:
            Tuple of (signed_url, expires_at)
            
        Raises:
            AzureError: If SAS generation fails
        """
        try:
            blob_client = self._client.get_blob_client(
                container=self._container_name,
                blob=blob_path,
            )
            
            # Calculate expiry time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self._container_name,
                blob_name=blob_path,
                account_key=self._client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expires_at,
            )
            
            # Construct full URL with SAS token
            signed_url = f"{blob_client.url}?{sas_token}"
            
            logger.debug(
                f"Generated SAS URL for blob: {blob_path}",
                extra={"blob_path": blob_path, "expires_at": expires_at.isoformat()},
            )
            
            return signed_url, expires_at
            
        except AzureError as e:
            logger.error(
                f"Failed to generate SAS URL: {e}",
                exc_info=True,
                extra={"blob_path": blob_path},
            )
            raise
    
    def delete_artifact(self, blob_path: str) -> bool:
        """Delete an artifact from blob storage.
        
        Args:
            blob_path: The blob path to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            blob_client = self._client.get_blob_client(
                container=self._container_name,
                blob=blob_path,
            )
            
            blob_client.delete_blob()
            logger.info(f"Deleted artifact: {blob_path}")
            return True
            
        except AzureError as e:
            if "BlobNotFound" in str(e):
                logger.warning(f"Blob not found for deletion: {blob_path}")
                return False
            logger.error(f"Failed to delete artifact: {e}", exc_info=True)
            raise
    
    def get_artifact_metadata(self, blob_path: str) -> Optional[dict]:
        """Get metadata for an artifact.
        
        Args:
            blob_path: The blob path
            
        Returns:
            Metadata dict or None if not found
        """
        try:
            blob_client = self._client.get_blob_client(
                container=self._container_name,
                blob=blob_path,
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "created_on": properties.creation_time,
                "last_modified": properties.last_modified,
                "metadata": properties.metadata,
            }
            
        except AzureError as e:
            if "BlobNotFound" in str(e):
                return None
            logger.error(f"Failed to get artifact metadata: {e}", exc_info=True)
            raise
