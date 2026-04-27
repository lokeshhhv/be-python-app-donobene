from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Any, Optional

from src.schemas.ClothesRequestPayload import ClothesRequestPayload
from src.models.clothes import ClothesRequest, ClothesRequestBeneficiaries, ClothesRequestBeneficiariesSizes
from src.models.clothes import ClothingSizeRow
from src.models.clothes import ClothingCategory
from src.models.clothes import ClothesAgeGroup
from src.models.types import Attachment, RequestCategory


from src.db.session import get_db
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
    prefix="/api/v1/clothes",
    tags=["Clothes Categories"],
    # dependencies=[Depends(get_current_user_id)],
)

@router.get("/clothes-age-groups", response_model=dict)
async def get_clothes_age_groups(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ClothesAgeGroup))
        clothes_age_groups = result.scalars().all()
        return success_response(data=[{"id": cag.id, "name": cag.name} for cag in clothes_age_groups], message="Fetched clothes age groups")
    except Exception as e:
        logger.error(f"Error in get_clothes_age_groups: {e}")
        return error_response(message="Failed to fetch clothes age groups", error=str(e))

@router.get("/clothes-categories", response_model=dict)
async def get_clothes_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ClothingCategory))
        clothes_categories = result.scalars().all()
        return success_response(data=[{"id": cc.id, "name": cc.name} for cc in clothes_categories], message="Fetched clothes categories")
    except Exception as e:
        logger.error(f"Error in get_clothes_categories: {e}")
        return error_response(message="Failed to fetch clothes categories", error=str(e))

@router.get("/clothes-size-rows", response_model=dict)
async def get_clothes_size_rows(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ClothingSizeRow))
        clothes_size_rows = result.scalars().all()
        return success_response(data=[{"id": csr.id, "name": csr.name} for csr in clothes_size_rows], message="Fetched clothes size rows")
    except Exception as e:
        logger.error(f"Error in get_clothes_size_rows: {e}")
        return error_response(message="Failed to fetch clothes size rows", error=str(e))

@router.post("/clothes-request", response_model=dict)
async def create_full_clothes_request(
    payload: ClothesRequestPayload, 
    db: AsyncSession = Depends(get_db)):
    try:
        # 1️⃣ Create main request
        new_request = ClothesRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id,
            # amount_requested=payload.amount_requested,
        )
        db.add(new_request)
        await db.flush()  # get request ID

        # 2️⃣ Loop beneficiaries
        for ben in payload.beneficiaries:
            verification_document_id = None
            beneficiary_photo_id = None

            # Create verification_document attachment if present
            if ben.verification_document is not None:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=ben.verification_document.document_type_id,
                    file_path=ben.verification_document.file_path
                )
                db.add(att)
                await db.flush()
                verification_document_id = att.id

            # Create beneficiary_photo attachment if present
            if ben.beneficiary_photo is not None:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=ben.beneficiary_photo.document_type_id,
                    file_path=ben.beneficiary_photo.file_path
                )
                db.add(att)
                await db.flush()
                beneficiary_photo_id = att.id

            # 3️⃣ Create beneficiary
            new_beneficiary = ClothesRequestBeneficiaries(
                clothes_request_id=new_request.id,
                person_name=ben.person_name,
                age_group=ben.age_group,
                gender_preference=ben.gender_preference,
                clothing_category_id=ben.clothing_category_id,
                need_by_date=ben.need_by_date,
                urgency_level_id=ben.urgency_level_id,
                verification_document_id=verification_document_id,
                beneficiary_photo_id=beneficiary_photo_id,
                amount_requested=ben.amount_requested
            )
            db.add(new_beneficiary)
            await db.flush()

            # 4️⃣ Add sizes
            for size in ben.sizes:
                new_size = ClothesRequestBeneficiariesSizes(
                    beneficiary_id=new_beneficiary.id,
                    clothing_type=size.clothing_type,
                    size_id=size.size_id,
                    quantity=size.quantity
                )
                db.add(new_size)

        # 5️⃣ Commit everything
        await db.commit()
        return success_response(data={"request_id": new_request.id}, message="Clothes request created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_full_clothes_request: {e}")
        return error_response(message="Failed to create clothes request", error=str(e))
