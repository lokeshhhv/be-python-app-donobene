import random
from typing import Optional
import redis.asyncio as redis
from src.config.settings import settings

# Redis connection pool (singleton)
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis():
    return redis.Redis(connection_pool=redis_pool)

async def generate_otp() -> str:
    """Generate a 6-digit random OTP as a string."""
    return f"{random.randint(100000, 999999):06d}"

async def save_otp(phone: str, otp: str) -> None:
    """Save OTP to Redis with 5 min TTL (key: otp:{phone})."""
    r = get_redis()
    await r.set(f"otp:{phone}", otp, ex=300)

async def get_otp(phone: str) -> Optional[str]:
    """Get OTP from Redis for a phone number."""
    r = get_redis()
    otp = await r.get(f"otp:{phone}")
    return otp

async def delete_otp(phone: str) -> None:
    """Delete OTP from Redis for a phone number."""
    r = get_redis()
    await r.delete(f"otp:{phone}")