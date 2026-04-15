import logging
import aiosmtplib
from email.message import EmailMessage
from typing import Optional
import os

logger = logging.getLogger("email_service")

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_pass]):
            raise ValueError("SMTP environment variables are not fully set.")

    async def send_email_with_attachment(
        self,
        subject: str,
        sender: str,
        recipient: str,
        body: str,
        attachment_bytes: bytes,
        attachment_filename: str,
        subtype: str = "pdf"
    ) -> None:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)
        msg.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype=subtype,
            filename=attachment_filename
        )
        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_pass,
                start_tls=True
            )
            logger.info(f"Email sent to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise RuntimeError(f"Failed to send email: {e}")
