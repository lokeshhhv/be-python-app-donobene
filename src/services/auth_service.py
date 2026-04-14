from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.types import SwitchUser, User
from src.schemas.auth import (
    RegisterRequest, TokenResponse, SendOTPRequest, OTPSentResponse, VerifyOTPRequest, RefreshTokenRequest, NewAccessTokenResponse, UserInfo
)
from src.utils.hashing import hash_password, verify_password
from src.utils.otp import generate_otp, save_otp, get_otp, delete_otp
import redis.asyncio as redis
import os
import smtplib
from email.mime.text import MIMEText
from src.core.jwt import create_access_token
from fastapi import BackgroundTasks

# Async Redis client (singleton)
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)

async def generate_email_otp(length: int = 4) -> str:
    import random
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

async def save_email_otp(email: str, otp: str, expires: int = 300) -> None:
    await redis_client.set(f"email_otp:{email}", otp, ex=expires)

async def get_email_otp(email: str) -> str:
    return await redis_client.get(f"email_otp:{email}")

async def delete_email_otp(email: str) -> None:
    await redis_client.delete(f"email_otp:{email}")

def send_otp_email(email: str, otp: str):
    smtp_user = os.getenv("EMAIL_USER")
    smtp_pass = os.getenv("EMAIL_PASS")
    if not smtp_user or not smtp_pass:
        raise Exception("Email credentials not set in environment variables.")
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Your Login OTP"
    msg["From"] = smtp_user
    msg["To"] = email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [email], msg.as_string())
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")

# Endpoint logic for POST /login (email)
async def login_with_email_otp(email: str, background_tasks: BackgroundTasks):
    otp = await generate_email_otp()
    try:
        await save_email_otp(email, otp)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to store OTP. Try again later.")
    try:
        background_tasks.add_task(send_otp_email, email, otp)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send OTP email.")
    return {"message": "OTP sent to email"}

# Endpoint logic for POST /verify-otp (email)
async def verify_email_otp_and_login(email: str, otp: str):
    stored_otp = await get_email_otp(email)
    if not stored_otp:
        raise HTTPException(status_code=410, detail="OTP expired or not found")
    if stored_otp != otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")
    await delete_email_otp(email)
    # You may want to check if user exists, or create user here
    # For demo, just issue JWT with email as subject
    access_token = create_access_token({"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}
from src.core.jwt import create_access_token, create_refresh_token, decode_token
from src.db.session import get_db
from datetime import datetime

# 1. Register User
async def register_user(payload: RegisterRequest, db: AsyncSession) -> TokenResponse:
    # Check if email exists
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check if phone exists
    result = await db.execute(select(User).where(User.phone == payload.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Phone already registered")

    hashed_pw = hash_password(payload.password)
    # 1. Create user first (without attachment_id)
    user = User(
        name=payload.name.strip(),
        email=payload.email,
        phone=payload.phone,
        password_hash=hashed_pw,
        type_donor_id=payload.type_donor_id,
        donor_type_subtype=payload.donor_type_subtype,
        organization_name=payload.organization_name,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 2. If attachment present, create it with user_id, then update user
    if payload.attachment:
        from src.models.types import Attachment
        att = Attachment(
            user_id=user.id,
            request_id=0,  # not linked to a request, or set as needed
            category_id=payload.attachment.get("category_id", 0), #₹ default to 0 if not provided
            document_type_id=payload.attachment["document_type_id"],
            file_path=payload.attachment["file_path"]
        )
        db.add(att)
        await db.commit()
        await db.refresh(att)
        user.attachment_id = att.id
        db.add(user)
        await db.commit()
        await db.refresh(user)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id), "phone": user.phone})
    refresh_token = create_refresh_token({"sub": str(user.id), "phone": user.phone})

    return TokenResponse(
        message="Registration successful",
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo.model_validate(user)
    )

# 2. Send OTP
async def send_otp(payload: SendOTPRequest, db: AsyncSession) -> OTPSentResponse:
    result = await db.execute(select(User).where(User.phone == payload.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Phone not registered")
    otp = await generate_otp()
    print(f"Generated OTP for {payload.phone}: {otp}")  # For testing, remove in production
    await save_otp(payload.phone, otp)
    return OTPSentResponse(message="OTP sent successfully", otp=otp)

# 3. Verify OTP Login
async def verify_otp_login(payload: VerifyOTPRequest, db: AsyncSession) -> TokenResponse:
    otp = await get_otp(payload.phone)
    if otp is None:
        raise HTTPException(status_code=410, detail="OTP expired")
    if otp != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")
    await delete_otp(payload.phone)
    result = await db.execute(select(User).where(User.phone == payload.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = create_access_token({"sub": str(user.id), "phone": user.phone})
    refresh_token = create_refresh_token({"sub": str(user.id), "phone": user.phone})
    user_last_logged_as_result = await db.execute(select(SwitchUser).where(SwitchUser.user_id == user.id))
    user_last_logged_as_obj = user_last_logged_as_result.scalar_one_or_none()
    user_last_logged_as = str(user_last_logged_as_obj.switched_to_type) if user_last_logged_as_obj else None
    return TokenResponse(
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo.model_validate({**user.__dict__, "last_logged_as": user_last_logged_as}),
    )

# 4. Refresh Access Token
async def refresh_access_token(payload: RefreshTokenRequest) -> NewAccessTokenResponse:
    data = decode_token(payload.refresh_token)
    user_id = data["sub"]
    phone = data["phone"]
    access_token = create_access_token({"sub": user_id, "phone": phone})
    return NewAccessTokenResponse(access_token=access_token)