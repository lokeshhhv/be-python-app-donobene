from pydantic import BaseModel
from typing import List, Optional


class AttachmentPayload(BaseModel):
    document_type_id: int
    file_path: str


class ShelterBeneficiaryPayload(BaseModel):
    person_name: Optional[str] = None
    total_members: Optional[int] = None

    special_need_id: Optional[int] = None
    staying_type_id: Optional[int] = None

    current_address: Optional[str] = None
    duration_of_problem: Optional[str] = None

    requirement_type_id: Optional[int] = None
    duration_option_id: Optional[int] = None
    number_of_days: Optional[int] = None

    verification_document: Optional[AttachmentPayload] = None
    damage_document: Optional[AttachmentPayload] = None


class ShelterRequestPayload(BaseModel):
    user_id: int
    category_id: int
    request_title: str
    request_description: Optional[str]

    status_id: Optional[int]
    urgency_id: Optional[int]

    verified: Optional[bool] = False
    reject_reason: Optional[str] = None

    beneficiaries: List[ShelterBeneficiaryPayload]