from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import date


class AttachmentPayload(BaseModel):
    document_type_id: int
    file_path: str


class PatientPayload(BaseModel):
    patient_name: str
    age: Optional[int] = None
    gender_id: Optional[int] = None

    medical_condition: Optional[str] = None
    blood_group_id: Optional[int] = None
    medical_category_id: Optional[int] = None

    # 🏥 hospital merged
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    doctor_name: Optional[str] = None

    financial_information: Optional[str] = None
    amount_paid: Optional[Decimal] = None
    amount_requested: Optional[Decimal] = None
    funds_needed_by: Optional[date] = None

    contact_information: Optional[str] = None
    emergency_contact_name: Optional[str] = None

    # 🔥 JSON
    support_type_ids: List[int] = []

    # 📎 attachments
    attachment: Optional[AttachmentPayload] = None
    prescription: Optional[AttachmentPayload] = None
    estimation: Optional[AttachmentPayload] = None


class MedicalRequestPayload(BaseModel):
    user_id: int
    category_id: int

    request_title: str
    request_description: Optional[str] = None

    status_id: Optional[int] = None
    urgency_id: Optional[int] = None

    patients: List[PatientPayload]