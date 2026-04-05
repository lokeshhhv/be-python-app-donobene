from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class SupportTypePayload(BaseModel):
    support_type_id: int


class SportsBeneficiaryPayload(BaseModel):
    person_name: Optional[str] = None
    age_group: Optional[str] = None
    gender_id: Optional[int] = None

    playing_level_id: int
    sports_category_id: int

    achievement: Optional[str] = None

    amount_requested: Optional[float] = None
    event_date: Optional[date] = None

    institution_name: Optional[str] = None
    phone: Optional[str] = None

    verification_document_id: Optional[int] = None
    achievement_document_id: Optional[int] = None

    support_types: List[SupportTypePayload] = Field(default_factory=list)


class SportsRequestPayload(BaseModel):
    user_id: int
    category_id: int

    request_title: str
    request_description: Optional[str] = None

    beneficiaries: List[SportsBeneficiaryPayload]