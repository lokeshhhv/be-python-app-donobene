from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class InvoiceRequest(BaseModel):
    request_id: str = Field(..., example="REQ20260219")
    name: str = Field(..., example="Nitesh Sharma")
    invoice_date: date = Field(..., example="2026-02-19")
    email: EmailStr = Field(..., example="official.lokeshvenkatraman@gmail.com")
    amount: float = Field(..., example=0)
    description: Optional[str] = Field(None, example="Food delivery for 50 children at orphanage")
    submitted_date: str = Field(..., example="2026-02-19")
    request_type: str = Field(..., example="Cooked Food")
    urgency: str = Field(..., example="High")
    verified_status: str = Field(..., example="✔ Verified")
    approved_by: str = Field(..., example="Admin")
    status: str = Field(..., example="Approved")
    receiver_type: str = Field(..., example="Helping Hands NGO")
    receiver_address: str = Field(..., example="123 Main St, Anytown, India")
    last_request: str = Field(..., example="2026-02-15")
    signature_date: str = Field(..., example="2026-02-20")
    receiver_name: str = Field(..., example="Nitesh Sharma")
