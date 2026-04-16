from pydantic import BaseModel

class VerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str
