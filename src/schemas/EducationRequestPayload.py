from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class AttachmentPayload(BaseModel):
    document_type_id: int
    file_path: str


class StudentPayload(BaseModel):
    person_name: str
    age: int
    grade_level: str

    education_support_type_id: int
    amount_requested: Optional[Decimal] = None

    institution_name: Optional[str] = None
    college_id: Optional[str] = None
    institution_address: Optional[str] = None

    contact_person_name: Optional[str] = None
    contact_person_phone: Optional[str] = None

    # 🔥 new way
    verification_document: Optional[AttachmentPayload] = None
    education_support_document: Optional[AttachmentPayload] = None


class EducationRequestPayload(BaseModel):
    user_id: int
    category_id: int

    request_title: str
    request_description: Optional[str] = None

    status_id: Optional[int] = None
    urgency_id: Optional[int] = None

    students: List[StudentPayload]