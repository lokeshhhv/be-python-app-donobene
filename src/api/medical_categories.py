from http.client import HTTPException
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.types import Attachment, RequestCategory, User
from src.models.medical import BloodGroup
from src.models.medical import MedicalRequestCategory
from src.models.medical import MedicalSupportType
from src.db.session import get_db

from src.models.medical import MedicalRequest
from src.models.medical import Patient
from src.schemas import MedicalRequestPayload
from src.schemas.MedicalRequestPayload import MedicalRequestPayload
from src.core.dependencies import get_current_user_id

import logging

# Configure logging
logger = logging.getLogger("api.types")
logging.basicConfig(level=logging.INFO)

# Global response helpers
def success_response(data: Any = None, message: str = "Success"):
    return {"success": True, "message": message, "data": data if data is not None else {}}

def error_response(message: str = "Error", error: Any = None):
    return {"success": False, "message": message, "error": error}

router = APIRouter(
    prefix="/api/v1/medical",
    tags=["Medical Categories"],
    # dependencies=[Depends(get_current_user_id)],
)

@router.get("/medical-categories", response_model=dict)
async def get_medical_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(MedicalRequestCategory))
        medical_categories = result.scalars().all()
        return success_response(data=[{"id": mc.id, "name": mc.name} for mc in medical_categories], message="Fetched medical categories")
    except Exception as e:
        logger.error(f"Error in get_medical_categories: {e}")
        return error_response(message="Failed to fetch medical categories", error=str(e))

@router.get("/support-types", response_model=dict)
async def get_support_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(MedicalSupportType))
        support_types = result.scalars().all()
        return success_response(data=[{"id": st.id, "name": st.name} for st in support_types], message="Fetched support types")
    except Exception as e:
        logger.error(f"Error in get_support_types: {e}")
        return error_response(message="Failed to fetch support types", error=str(e))

@router.get("/blood-groups", response_model=dict)
async def get_blood_groups(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(BloodGroup))
        blood_groups = result.scalars().all()
        return success_response(data=[{"id": bg.id, "name": bg.name} for bg in blood_groups], message="Fetched blood groups")
    except Exception as e:
        logger.error(f"Error in get_blood_groups: {e}")
        return error_response(message="Failed to fetch blood groups", error=str(e))


@router.post("/medical-request", response_model=dict)
async def create_medical_request(
    payload: MedicalRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        async def _exists(model, value: int):
            result = await db.execute(select(model.id).where(model.id == value))
            return result.scalar_one_or_none() is not None

        # ✅ Validate main
        if not await _exists(User, payload.user_id):
            return error_response(message="Invalid user_id")

        if not await _exists(RequestCategory, payload.category_id):
            return error_response(message="Invalid category_id")

        # ✅ Create request
        new_request = MedicalRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id
        )
        db.add(new_request)
        await db.flush()

        # ✅ Patients
        for i, p in enumerate(payload.patients, start=1):
            # 🔥 attachments
            attachment_id = None
            prescription_id = None
            estimation_id = None

            if p.attachment:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=p.attachment.document_type_id,
                    file_path=p.attachment.file_path
                )
                db.add(att)
                await db.flush()
                attachment_id = att.id

            if p.prescription:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=p.prescription.document_type_id,
                    file_path=p.prescription.file_path
                )
                db.add(att)
                await db.flush()
                prescription_id = att.id

            if p.estimation:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=p.estimation.document_type_id,
                    file_path=p.estimation.file_path
                )
                db.add(att)
                await db.flush()
                estimation_id = att.id

            db.add(
                Patient(
                    medical_request_id=new_request.id,
                    patient_name=p.patient_name,
                    age=p.age,
                    gender_id=p.gender_id,
                    medical_condition=p.medical_condition,
                    blood_group_id=p.blood_group_id,
                    medical_category_id=p.medical_category_id,

                    hospital_name=p.hospital_name,
                    hospital_address=p.hospital_address,
                    doctor_name=p.doctor_name,
                    financial_information=p.financial_information,
                    amount_paid=p.amount_paid,
                    amount_requested=p.amount_requested,
                    funds_needed_by=p.funds_needed_by,
                    contact_information=p.contact_information,
                    emergency_contact_name=p.emergency_contact_name,

                    support_type_ids=p.support_type_ids,

                    attachment_id=attachment_id,
                    prescription_id=prescription_id,
                    estimation_id=estimation_id
                )
            )

        await db.commit()
        return success_response(data={"request_id": new_request.id}, message="Medical request created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_medical_request: {e}")
        return error_response(message="Failed to create medical request", error=str(e))
    
