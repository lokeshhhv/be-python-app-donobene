
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional

# REQUEST SCHEMAS

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    type_donor_id: Optional[int] = None
    donor_type_subtype: Optional[int] = None
    organization_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    attachment: Optional[dict] = None  # expects {file_path, document_type_id, category_id}

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be 72 bytes or less (bcrypt limit)")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least 1 lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least 1 number")
        return v

class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# RESPONSE SCHEMAS

class UserInfo(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    organization_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    type_donor_id: Optional[int]
    donor_type_subtype: Optional[int]
    last_logged_as: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo

class OTPSentResponse(BaseModel):
    message: str
    otp: str  # Dev only — remove in production

class NewAccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ErrorResponse(BaseModel):
    detail: str
