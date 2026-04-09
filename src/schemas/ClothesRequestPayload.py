from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class AttachmentPayload(BaseModel):
    document_type_id: int
    file_path: str

class SizePayload(BaseModel):
    clothing_type: str
    size_id: int
    quantity: int

class BeneficiaryPayload(BaseModel):
    person_name: str
    age_group: int
    gender_preference: int
    clothing_category_id: int
    need_by_date: date
    urgency_level_id: int
    verification_document: Optional[AttachmentPayload] = None  # object, not ID
    beneficiary_photo: Optional[AttachmentPayload] = None      # object, not ID
    sizes: List[SizePayload]

class ClothesRequestPayload(BaseModel):
    user_id: int
    category_id: int
    request_title: str
    request_description: Optional[str] = None
    status_id: Optional[int] = None
    urgency_id: Optional[int] = None
    beneficiaries: List[BeneficiaryPayload]

