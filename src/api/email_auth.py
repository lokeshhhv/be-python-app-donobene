from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from src.utils.email_otp import generate_otp, save_otp, get_otp, delete_otp, send_otp_email
from src.core.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", status_code=200)
async def login(request: LoginRequest):
    otp = await generate_otp()
    await save_otp(request.email, otp)
    try:
        await send_otp_email(request.email, otp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP email: {e}")
    return {"message": "OTP sent to your email"}

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: VerifyOTPRequest):
    stored_otp = await get_otp(request.email)
    if not stored_otp:
        raise HTTPException(status_code=410, detail="OTP expired or not found")
    if stored_otp != request.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")
    await delete_otp(request.email)
    # You can add user lookup/creation logic here if needed
    access_token = create_access_token({"sub": request.email})
    return TokenResponse(access_token=access_token)
