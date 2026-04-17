from typing import Optional
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

router = APIRouter(
    prefix="/api/v1/sports",
    tags=["Sports Categories"],
    # dependencies=[Depends(get_current_user_id)],
)

# ===========================
# ✅ MASTER GET APIs
# ===========================

@router.get("/sports-categories", response_model=list[dict])
async def get_sports_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SportsCategory))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data]


@router.get("/support-types", response_model=list[dict])
async def get_sports_support_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SportsSupportType))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data]


@router.get("/playing-levels", response_model=list[dict])
async def get_playing_levels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlayingLevel))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data]


# ===========================
# ✅ POST API
# ===========================

@router.post("/sports-request")
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
            raise HTTPException(400, "Invalid user_id")

        if not await _exists(RequestCategory, payload.category_id):
            raise HTTPException(400, "Invalid category_id")

        # ===========================
        # ✅ CREATE REQUEST
        # ===========================

        new_request = SportsRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description
        )

        db.add(new_request)
        await db.flush()

        # ===========================
        # ✅ BENEFICIARIES
        # ===========================

        for i, ben in enumerate(payload.beneficiaries, start=1):

            # ---- validations ----
            if ben.gender_id and not await _exists(Gender, ben.gender_id):
                raise HTTPException(400, f"Invalid gender_id at beneficiaries[{i}]")

            if not await _exists(PlayingLevel, ben.playing_level_id):
                raise HTTPException(400, f"Invalid playing_level_id at beneficiaries[{i}]")

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
                urgency_id=ben.urgency_id,
                status_id=ben.status_id,
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

        return {
            "message": "Sports request created successfully",
            "request_id": new_request.id
        }

    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Foreign key error")

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))

# ===========================
# ✅ GET API (LIST)
# ===========================

# @router.get("/sports-request")
# async def get_sports_requests(user_id: int, db: AsyncSession = Depends(get_db)):

#     # ✅ Fetch all requests
#     result = await db.execute(select(SportsRequest).where(SportsRequest.user_id == user_id))
#     requests = result.scalars().all()

#     response = []

#     for r in requests:

#         # ✅ Fetch beneficiaries
#         ben_result = await db.execute(
#             select(SportsRequestBeneficiary).where(
#                 SportsRequestBeneficiary.sports_request_id == r.id
#             )
#         )
#         beneficiaries = ben_result.scalars().all()

#         ben_data = []

#         for b in beneficiaries:

#             # 🔥 fetch attachments
#             verification_doc = None
#             achievement_doc = None

#             if b.verification_document_id:
#                 res = await db.execute(
#                     select(Attachment).where(Attachment.id == b.verification_document_id)
#                 )
#                 att = res.scalar_one_or_none()
#                 if att:
#                     verification_doc = {
#                         "id": att.id,
#                         "file_path": att.file_path
#                     }

#             if b.achievement_document_id:
#                 res = await db.execute(
#                     select(Attachment).where(Attachment.id == b.achievement_document_id)
#                 )
#                 att = res.scalar_one_or_none()
#                 if att:
#                     achievement_doc = {
#                         "id": att.id,
#                         "file_path": att.file_path
#                     }

#             ben_data.append({
#                 "id": b.id,
#                 "person_name": b.person_name,
#                 "age_group": b.age_group,
#                 "gender_id": b.gender_id,
#                 "playing_level_id": b.playing_level_id,
#                 "sports_category_ids": b.sports_category_ids,
#                 "support_type_ids": b.support_type_ids,
#                 "achievement": b.achievement,
#                 "amount_requested": b.amount_requested,
#                 "event_date": b.event_date,
#                 "institution_name": b.institution_name,
#                 "phone": b.phone,

#                 # 🔥 attachments added
#                 "verification_document": verification_doc,
#                 "achievement_document": achievement_doc
#             })

#         response.append({
#             "id": r.id,
#             "user_id": r.user_id,
#             "category_id": r.category_id,
#             "request_title": r.request_title,
#             "request_description": r.request_description,
#             "verified": r.verified,
#             "reject_reason": r.reject_reason,
#             "beneficiaries": ben_data
#         })

#     return response