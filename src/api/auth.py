from typing import Any

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.auth import (
    RegisterRequest, RegisterResponse, TokenResponse, SendOTPRequest, OTPSentResponse,
    VerifyOTPRequest, RefreshTokenRequest, NewAccessTokenResponse, ErrorResponse
)
from src.services.auth_service import (
    register_user, send_otp, verify_otp_login, refresh_access_token
)
from src.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

import logging

# Configure logging
logger = logging.getLogger("api.types")
logging.basicConfig(level=logging.INFO)

# Global response helpers
def success_response(data: Any = None, message: str = "Success"):
    return {"success": True, "message": message, "data": data if data is not None else {}}

def error_response(message: str = "Error", error: Any = None):
    return {"success": False, "message": message, "error": error}


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
):
    try:
        data = await register_user(payload, db)
        return data
    except Exception as e:
        logger.error(f"Error in register: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post(
    "/login/send-otp",
    response_model=OTPSentResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def send_otp_route(
    payload: SendOTPRequest, db: AsyncSession = Depends(get_db)
):
    try:
        data = await send_otp(payload, db)
        return data
    except Exception as e:
        logger.error(f"Error in send_otp_route: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@router.post(
    "/login/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={410: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def verify_otp_route(
    payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)
):
    try:
        data = await verify_otp_login(payload, db)
        return data
    except Exception as e:
        logger.error(f"Error in verify_otp_route: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


@router.post(
    "/refresh",
    response_model=NewAccessTokenResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {"model": ErrorResponse}},
)
async def refresh_token_route(
    payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    try:
        data = await refresh_access_token(payload, db)
        return data
    except Exception as e:
        logger.error(f"Error in refresh_token_route: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh access token")