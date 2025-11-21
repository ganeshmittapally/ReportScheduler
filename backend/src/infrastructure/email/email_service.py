"""Email delivery service using Azure Communication Services."""

import logging
from typing import Optional

from azure.communication.email import EmailClient
from azure.core.exceptions import AzureError

from src.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Azure Communication Services."""
    
    def __init__(self):
        """Initialize Email client."""
        if settings.ACS_CONNECTION_STRING:
            self._client = EmailClient.from_connection_string(
                settings.ACS_CONNECTION_STRING
            )
        else:
            logger.warning("ACS_CONNECTION_STRING not configured, email sending disabled")
            self._client = None
    
    def send_report_email(
        self,
        recipients: list[str],
        subject: str,
        artifact_url: str,
        report_name: str,
        execution_time: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> tuple[bool, Optional[str]]:
        """Send report delivery email with artifact link.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            artifact_url: Signed URL to download the report
            report_name: Name of the report
            execution_time: When the report was generated
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            
        Returns:
            Tuple of (success, message_id_or_error)
        """
        if not self._client:
            logger.warning("Email client not configured, skipping email delivery")
            return False, "Email service not configured"
        
        try:
            # Build HTML email body
            html_content = self._build_email_html(
                report_name=report_name,
                execution_time=execution_time,
                artifact_url=artifact_url,
            )
            
            # Build plain text fallback
            plain_text = self._build_email_text(
                report_name=report_name,
                execution_time=execution_time,
                artifact_url=artifact_url,
            )
            
            # Prepare message
            message = {
                "senderAddress": settings.EMAIL_FROM_ADDRESS,
                "recipients": {
                    "to": [{"address": email} for email in recipients],
                },
                "content": {
                    "subject": subject,
                    "plainText": plain_text,
                    "html": html_content,
                },
            }
            
            # Add CC if provided
            if cc:
                message["recipients"]["cc"] = [{"address": email} for email in cc]
            
            # Add BCC if provided
            if bcc:
                message["recipients"]["bcc"] = [{"address": email} for email in bcc]
            
            # Send email
            poller = self._client.begin_send(message)
            result = poller.result()
            
            logger.info(
                f"Email sent successfully: {result.message_id}",
                extra={
                    "message_id": result.message_id,
                    "recipients": recipients,
                    "subject": subject,
                },
            )
            
            return True, result.message_id
            
        except AzureError as e:
            logger.error(
                f"Failed to send email: {e}",
                exc_info=True,
                extra={"recipients": recipients, "subject": subject},
            )
            return False, str(e)
        except Exception as e:
            logger.error(
                f"Unexpected error sending email: {e}",
                exc_info=True,
                extra={"recipients": recipients, "subject": subject},
            )
            return False, str(e)
    
    def _build_email_html(
        self,
        report_name: str,
        execution_time: str,
        artifact_url: str,
    ) -> str:
        """Build HTML email content.
        
        Args:
            report_name: Name of the report
            execution_time: When the report was generated
            artifact_url: URL to download the report
            
        Returns:
            HTML email content
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1976D2; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #1976D2; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Report is Ready</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Your scheduled report <strong>{report_name}</strong> has been generated successfully.</p>
                    <p><strong>Generated at:</strong> {execution_time}</p>
                    <p>Click the button below to download your report:</p>
                    <div style="text-align: center;">
                        <a href="{artifact_url}" class="button">Download Report</a>
                    </div>
                    <p><em>Note: This link will expire in 24 hours.</em></p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Report Scheduler.</p>
                    <p>If you have questions, please contact your system administrator.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_email_text(
        self,
        report_name: str,
        execution_time: str,
        artifact_url: str,
    ) -> str:
        """Build plain text email content.
        
        Args:
            report_name: Name of the report
            execution_time: When the report was generated
            artifact_url: URL to download the report
            
        Returns:
            Plain text email content
        """
        return f"""
Your Report is Ready

Hello,

Your scheduled report "{report_name}" has been generated successfully.

Generated at: {execution_time}

Download your report:
{artifact_url}

Note: This link will expire in 24 hours.

---
This is an automated message from Report Scheduler.
If you have questions, please contact your system administrator.
        """.strip()
