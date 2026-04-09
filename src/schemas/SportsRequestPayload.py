from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class AttachmentPayload(BaseModel):
    document_type_id: int
    file_path: str


class SportsBeneficiaryPayload(BaseModel):
    person_name: Optional[str]
    age_group: Optional[str]
    gender_id: Optional[int]

    playing_level_id: int

    sports_category_ids: List[int]
    support_type_ids: List[int]

    achievement: Optional[str]
    amount_requested: Optional[int]
    event_date: Optional[date]

    institution_name: Optional[str]
    phone: Optional[str]

    verification_document: Optional[AttachmentPayload]
    achievement_document: Optional[AttachmentPayload]

    urgency_id: Optional[int]
    status_id: Optional[int]


class SportsRequestPayload(BaseModel):
    user_id: int
    category_id: int
    request_title: str
    request_description: Optional[str]

    beneficiaries: List[SportsBeneficiaryPayload]