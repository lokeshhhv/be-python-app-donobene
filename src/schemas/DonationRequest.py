from pydantic import BaseModel, EmailStr

class DonationRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    amount: float
