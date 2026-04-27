from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.types import Attachment, RequestStatusMaster, UrgencyLevel, User
from src.models.types import RequestCategory
from src.models.types import Gender
from src.schemas.SportsRequestPayload import SportsRequestPayload
from src.db.session import get_db

# ✅ Master Tables
from src.models.sports import SportsCategory
from src.models.sports import SportsSupportType
from src.models.sports import PlayingLevel

from src.models.sports import SportsRequest
from src.models.sports import SportsRequestBeneficiary
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
    prefix="/api/v1/sports",
    tags=["Sports Categories"],
    # dependencies=[Depends(get_current_user_id)],
)

# ===========================
# ✅ MASTER GET APIs
# ===========================

@router.get("/sports-categories", response_model=dict)
async def get_sports_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(SportsCategory))
        data = result.scalars().all()
        return success_response(data=[{"id": d.id, "name": d.name} for d in data], message="Fetched sports categories")
    except Exception as e:
        logger.error(f"Error in get_sports_categories: {e}")
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch sports categories", str(e)))


@router.get("/support-types", response_model=dict)
async def get_sports_support_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(SportsSupportType))
        data = result.scalars().all()
        return success_response(data=[{"id": d.id, "name": d.name} for d in data], message="Fetched support types")
    except Exception as e:
        logger.error(f"Error in get_sports_support_types: {e}")
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch support types", str(e)))


@router.get("/playing-levels", response_model=dict)
async def get_playing_levels(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(PlayingLevel))
        data = result.scalars().all()
        return success_response(data=[{"id": d.id, "name": d.name} for d in data], message="Fetched playing levels")
    except Exception as e:
        logger.error(f"Error in get_playing_levels: {e}")
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch playing levels", str(e)))


# ===========================
# ✅ POST API
# ===========================

@router.post("/sports-request", response_model=dict)
async def create_sports_request(
    payload: SportsRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        async def _exists(model, value: int):
            result = await db.execute(select(model.id).where(model.id == value))
            return result.scalar_one_or_none() is not None

        # ===========================
        # ✅ VALIDATION
        # ===========================
        if not await _exists(User, payload.user_id):
            return error_response(message="Invalid user_id")

        if not await _exists(RequestCategory, payload.category_id):
            return error_response(message="Invalid category_id")

        # ===========================
        # ✅ CREATE REQUEST
        # ===========================
        new_request = SportsRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description,
            urgency_id=payload.urgency_id,
            status_id=payload.status_id
        )
        db.add(new_request)
        await db.flush()

        # ===========================
        # ✅ BENEFICIARIES
        # ===========================
        for i, ben in enumerate(payload.beneficiaries, start=1):
            # ---- validations ----
            if ben.gender_id and not await _exists(Gender, ben.gender_id):
                return error_response(message=f"Invalid gender_id at beneficiaries[{i}]")

            if not await _exists(PlayingLevel, ben.playing_level_id):
                return error_response(message=f"Invalid playing_level_id at beneficiaries[{i}]")

            # ===========================
            # 🔥 CREATE ATTACHMENTS
            # ===========================
            verification_id = None
            achievement_id = None

            if ben.verification_document:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=ben.verification_document.document_type_id,
                    file_path=ben.verification_document.file_path
                )
                db.add(att)
                await db.flush()
                verification_id = att.id

            if ben.achievement_document:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=ben.achievement_document.document_type_id,
                    file_path=ben.achievement_document.file_path
                )
                db.add(att)
                await db.flush()
                achievement_id = att.id

            # ===========================
            # ✅ CREATE BENEFICIARY
            # ===========================
            new_ben = SportsRequestBeneficiary(
                sports_request_id=new_request.id,
                person_name=ben.person_name,
                age_group=ben.age_group,
                gender_id=ben.gender_id,
                playing_level_id=ben.playing_level_id,
                achievement=ben.achievement,
                amount_requested=ben.amount_requested,
                event_date=ben.event_date,
                institution_name=ben.institution_name,
                phone=ben.phone,
                verification_document_id=verification_id,
                achievement_document_id=achievement_id,
                sports_category_ids=ben.sports_category_ids,
                support_type_ids=ben.support_type_ids
            )
            db.add(new_ben)

        # ===========================
        # ✅ COMMIT
        # ===========================
        await db.commit()
        return success_response(data={"request_id": new_request.id}, message="Sports request created successfully")
    except IntegrityError:
        await db.rollback()
        logger.error("Foreign key error in create_sports_request")
        return error_response(message="Foreign key error")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_sports_request: {e}")
        return error_response(message="Failed to create sports request", error=str(e))
