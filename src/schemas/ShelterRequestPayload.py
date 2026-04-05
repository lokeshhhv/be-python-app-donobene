from pydantic import BaseModel, Field
from typing import List, Optional


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

    verification_document_id: Optional[int] = None
    damage_document_id: Optional[int] = None


class ShelterRequestPayload(BaseModel):
    user_id: int
    category_id: int

    request_title: str
    request_description: Optional[str] = None

    status_id: Optional[int] = None
    urgency_id: Optional[int] = None

    beneficiaries: List[ShelterBeneficiaryPayload] = Field(default_factory=list)