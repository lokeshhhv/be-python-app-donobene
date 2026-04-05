from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class SizePayload(BaseModel):
    clothing_type: str
    size_id: int
    quantity: int

class BeneficiaryPayload(BaseModel):
    beneficiary_name: str
    person_name: str
    age_group: int
    gender_preference: int
    clothing_category_id: int
    additional_size_requirements: Optional[str]
    need_by_date: date
    urgency_level_id: int
    verification_document_id: Optional[int]
    beneficiary_photo_id: Optional[int]
    sizes: List[SizePayload]

class ClothesRequestPayload(BaseModel):
    user_id: int
    category_id: int
    request_title: str
    request_description: str
    status_id: int
    urgency_id: int
    beneficiaries: List[BeneficiaryPayload]
