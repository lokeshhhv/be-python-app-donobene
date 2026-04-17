
# --- Pydantic Response Model for User Profile ---

from pydantic import BaseModel
from typing import Optional, List, Any

class AttachmentResponse(BaseModel):
    id: int
    document_type_id: int
    user_id: int
    request_id: int
    file_path: str
    category_id: int
    created_at: Optional[str]

# --- Main models below ---
class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    organization_name: Optional[str]
    city: Optional[str]
    pincode: Optional[str]
    address: Optional[str]
    state: Optional[str]
    attachment: Optional[AttachmentResponse]
    type_donor_name: Optional[str]
    user_type_name: Optional[str]