from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.auth import (
    RegisterRequest, TokenResponse, SendOTPRequest, OTPSentResponse,
    VerifyOTPRequest, RefreshTokenRequest, NewAccessTokenResponse, ErrorResponse
)
from src.services.auth_service import (
    register_user, send_otp, verify_otp_login, refresh_access_token
)
from src.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
):
    return await register_user(payload, db)


@router.post(
    "/login/send-otp",
    response_model=OTPSentResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def send_otp_route(
    payload: SendOTPRequest, db: AsyncSession = Depends(get_db)
):
    return await send_otp(payload, db)


@router.post(
    "/login/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={410: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def verify_otp_route(
    payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)
):
    return await verify_otp_login(payload, db)


@router.post(
    "/refresh",
    response_model=NewAccessTokenResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {"model": ErrorResponse}},
)
async def refresh_token_route(
    payload: RefreshTokenRequest
):
    return await refresh_access_token(payload)