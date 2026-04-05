import os
import redis.asyncio as redis
import random
import smtplib
from email.mime.text import MIMEText
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

from src.config.settings import settings
EMAIL_ADDRESS = settings.EMAIL_USER
EMAIL_PASSWORD = settings.EMAIL_PASS

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def generate_otp(length: int = 4) -> str:
    return ''.join(random.choices('0123456789', k=length))

async def save_otp(email: str, otp: str, expires: int = 300) -> None:
    await redis_client.set(f"otp:{email}", otp, ex=expires)

async def get_otp(email: str) -> Optional[str]:
    return await redis_client.get(f"otp:{email}")

async def delete_otp(email: str) -> None:
    await redis_client.delete(f"otp:{email}")

async def send_otp_email(email: str, otp: str) -> None:
    subject = "Your Login OTP"
    body = f"Your OTP is: {otp} (valid for 5 minutes)"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [email], msg.as_string())
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")
