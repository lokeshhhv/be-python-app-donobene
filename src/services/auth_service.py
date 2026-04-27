from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.types import SwitchUser, User
from src.schemas.auth import (
    RegisterRequest, TokenResponse, SendOTPRequest, OTPSentResponse, VerifyOTPRequest, RefreshTokenRequest, NewAccessTokenResponse, UserInfo
)
from src.utils.hashing import hash_password
from src.utils.otp import generate_otp, save_otp, get_otp, delete_otp
import redis.asyncio as redis
import os
import smtplib
from email.mime.text import MIMEText
from src.core.jwt import create_access_token
from fastapi import BackgroundTasks
from src.config.settings import settings
# Async Redis client (singleton)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def generate_email_otp(length: int = 4) -> str:
    import random
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

async def save_email_otp(email: str, otp: str, expires: int = 300) -> None:
    await redis_client.set(f"email_otp:{email}", otp, ex=expires)

async def get_email_otp(email: str) -> str:
    return await redis_client.get(f"email_otp:{email}")

async def delete_email_otp(email: str) -> None:
    await redis_client.delete(f"email_otp:{email}")

def send_otp_email(email: str, otp: str, user_name: str = "User", verify_link: str = "#"):
    """
    Send OTP email using the HTML template.
    """
    from email.mime.multipart import MIMEMultipart
    smtp_user = settings.SMTP_USER
    smtp_pass = settings.SMTP_PASS
    if not smtp_user or not smtp_pass:
        raise Exception("Email credentials not set in environment variables.")
    html_content = render_otp_email_html(user_name, otp, verify_link)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Login OTP"
    msg["From"] = smtp_user
    msg["To"] = email
    msg.attach(MIMEText(html_content, "html"))
    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, 465) as server:
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
from src.schemas.auth import RegisterResponse

async def register_user(payload: RegisterRequest, db: AsyncSession) -> RegisterResponse:
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

    # Registration success, do not return tokens or user info
    return RegisterResponse(message="Registration successful")

# 2. Send OTP
async def send_otp(payload: SendOTPRequest, db: AsyncSession) -> OTPSentResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    otp = await generate_otp()
    print(f"Generated OTP for {payload.email}: {otp}")  # For testing, remove in production
    await save_otp(payload.email, otp)
    # Use user's name if available, else fallback to email prefix
    user_name = user.name if hasattr(user, "name") and user.name else payload.email.split("@")[0]
    # You can generate a real verify_link if needed
    verify_link = "#"
    send_otp_email(payload.email, otp, user_name, verify_link)
    return OTPSentResponse(message="OTP sent successfully", otp=otp)

# 3. Verify OTP Login
async def verify_otp_login(payload: VerifyOTPRequest, db: AsyncSession) -> TokenResponse:
    otp = await get_otp(payload.email)
    if otp is None:
        raise HTTPException(status_code=410, detail="OTP expired")
    if otp != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")
    await delete_otp(payload.email)
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})
    user_dict = user.__dict__.copy()
    user_dict["user_type_id"] = user_dict.get("type_donor_id")
    user_dict["user_subtype_id"] = user_dict.get("donor_type_subtype")
    return TokenResponse(
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo.model_validate(user_dict),
    )

# 4. Refresh Access Token
async def refresh_access_token(payload: RefreshTokenRequest, db: AsyncSession) -> NewAccessTokenResponse:
    print("[DEBUG] Starting refresh_access_token")
    try:
        data = decode_token(payload.refresh_token)
        print(f"[DEBUG] Decoded token data: {data}")
        user_id = data["sub"]
    except Exception as e:
        print(f"[DEBUG] Token decode failed: {e}")
        raise
    from sqlalchemy.future import select
    from src.models.types import User
    try:
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        print(f"[DEBUG] User lookup for id={user_id}: {user}")
    except Exception as e:
        print(f"[DEBUG] DB lookup failed: {e}")
        raise
    if not user:
        print(f"[DEBUG] No user found for id={user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    try:
        access_token = create_access_token({"sub": user_id})
        print(f"[DEBUG] Created new access token for user_id={user_id}")
    except Exception as e:
        print(f"[DEBUG] Access token creation failed: {e}")
        raise
    return NewAccessTokenResponse(access_token=access_token)

# --- OTP Email Template Renderer ---
def render_otp_email_html(user_name: str, otp: str, verify_link: str) -> str:
        """
        Render the OTP verification email HTML with the given user name, OTP, and verification link.
        """
        html_template = '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    <title>DonoBene OTP Verification</title>
                </head>
                <body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, sans-serif;">
                    <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8; padding:20px 0;">
                        <tr>
                            <td align="center">
                                <table width="420" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
                                    <tr>
                                        <td style="background:#2E7D32; padding:20px; text-align:center; color:#ffffff;">
                                            <h1 style="margin:0; font-size:22px;">DonoBene</h1>
                                            <p style="margin:5px 0 0; font-size:13px;">Connecting hearts through giving</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:30px 25px; color:#333333;">
                                            <h2 style="margin-top:0; font-size:18px;">Verify Your Email</h2>
                                            <p style="font-size:14px; line-height:1.6;">
                                                Hi <strong>{user_name}</strong>,
                                            </p>
                                            <p style="font-size:14px; line-height:1.6;">
                                                Use the One-Time Password (OTP) below to securely verify your DonoBene account:
                                            </p>
                                            <div style="margin:25px 0; text-align:center;">
                                                <span style="display:inline-block; background:#f1f3f5; padding:15px 30px; font-size:24px; letter-spacing:4px; border-radius:8px; font-weight:bold; color:#2E7D32;">
                                                    {otp}
                                                </span>
                                            </div>
                                            <p style="font-size:13px; color:#666;">
                                                This code is valid for <strong>5 minutes</strong>. Do not share it with anyone.
                                            </p>
                                            <p style="font-size:13px; color:#999;">
                                                If you didn’t request this, you can safely ignore this email.
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="border-top:1px solid #eeeeee;"></td>
                                    </tr>
                                    <tr>
                                        <td style="padding:20px; text-align:center; font-size:12px; color:#888;">
                                            <p style="margin:0;">
                                                © 2026 DonoBene. All rights reserved.
                                            </p>
                                            <p style="margin:5px 0;">
                                                Need help? <a href="mailto:support@donobene.com" style="color:#2E7D32; text-decoration:none;">Contact Support</a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
        '''
        return html_template.format(user_name=user_name, otp=otp, verify_link=verify_link)