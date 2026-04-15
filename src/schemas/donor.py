from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class DonationItem(BaseModel):
    items: str
    quantity: int
    unit_id: int


class VerificationDocumentPayload(BaseModel):
    document_type_id: int
    file_path: str

class FoodDonationCreate(BaseModel):
    user_id: int
    category_id: int
    donation_title: str
    delivery_preference_id: Optional[int]
    preferred_date: Optional[date]
    notes: Optional[str]
    items: List[DonationItem]
    verification_document: Optional[VerificationDocumentPayload] = None

# Clothes donation schemas would be similar to the above structure, with appropriate changes to fields and relationships.

class ClothesDonationDetailCreate(BaseModel):
    category_id: int
    size_id: int
    condition_id: int
    quantity: int


class ClothesDonationCreate(BaseModel):
    user_id: int
    category_id: int
    description: str

    pickup_type_id: Optional[int] = None
    available_date: Optional[date] = None
    verification_document: Optional[VerificationDocumentPayload] = None
    notes: Optional[str]

    details: List[ClothesDonationDetailCreate]


class MedicalDonationCategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    is_active: Optional[bool] = True



class DonorStemcellDonationSchema(BaseModel):
    id: int
    name: str



class DonorTissueDonationSchema(BaseModel):
    id: int
    name: str



class DonorOrganDonationSchema(BaseModel):
    id: int
    name: str



class DonorConsentTypeSchema(BaseModel):
    id: int
    name: str



class DonorAvailabilityTypeSchema(BaseModel):
    id: int
    name: str



class MedicalDonationCategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    is_active: Optional[bool]



class MedicalDonationCreate(BaseModel):
    user_id: int
    category_id: Optional[int] = None
    medical_donation_category_id: Optional[int] = None
    full_name: str
    age_group: str
    gender_id: int
    contact_number: str
    blood_group_id: Optional[int] = None
    # For milk donation only
    milk_volume: Optional[int] = None
    baby_age_months: Optional[int] = None
    # For medical supplies only
    supply_type: Optional[str] = None
    quantity: Optional[int] = None
    weight_kg: Optional[float] = None
    major_illness: Optional[bool] = False
    recent_surgery: Optional[bool] = False
    last_donation_date: Optional[date] = None
    currently_on_medication: Optional[bool] = False
    donation_type: str
    availability_type_id: Optional[int] = None
    consent_type_id: Optional[int] = None
    preferred_hospital: Optional[str] = None
    donation_location: Optional[str] = None
    organ_ids: Optional[List[int]] = None
    tissue_ids: Optional[List[int]] = None
    stemcell_ids: Optional[List[int]] = None

    @classmethod
    def validate_mutually_exclusive_ids(cls, values):
        cat_id = values.get('medical_donation_category_id')
        if cat_id is not None:
            # Example: 1=organ, 2=tissue, 3=stemcell (replace with your actual IDs)
            if cat_id == 1:
                values['tissue_ids'] = []
                values['stemcell_ids'] = []
            elif cat_id == 2:
                values['organ_ids'] = []
                values['stemcell_ids'] = []
            elif cat_id == 3:
                values['organ_ids'] = []
                values['tissue_ids'] = []
        return values

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_mutually_exclusive_ids

class MedicalDonationSchema(MedicalDonationCreate):
    id: int
    created_at: Optional[str]
