from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import date


# 🔹 Support Type
class PatientSupportTypePayload(BaseModel):
    support_type_id: int


# 🔹 Hospital Details
class HospitalDetailsPayload(BaseModel):
    hospital_name: str
    hospital_address: Optional[str] = None
    doctor_name: Optional[str] = None

    financial_information: Optional[str] = None
    amount_paid: Optional[Decimal] = None
    amount_requested: Optional[Decimal] = None
    funds_needed_by: Optional[date] = None

    contact_information: Optional[str] = None
    emergency_contact_name: Optional[str] = None

    attachment_id: Optional[int] = None
    prescription_id: Optional[int] = None
    estimation_id: Optional[int] = None


# 🔹 Patient
class PatientPayload(BaseModel):
    patient_name: str
    age: Optional[int] = None
    gender_id: Optional[int] = None

    medical_condition: Optional[str] = None

    blood_group_id: Optional[int] = None
    medical_category_id: Optional[int] = None

    support_types: List[PatientSupportTypePayload]
    hospital_details: HospitalDetailsPayload


# 🔹 Main Medical Request
class MedicalRequestPayload(BaseModel):
    user_id: int
    category_id: int

    request_title: str
    request_description: Optional[str] = None

    status_id: Optional[int] = None
    urgency_id: Optional[int] = None

    patients: List[PatientPayload]