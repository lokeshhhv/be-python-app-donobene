from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.types import Attachment, RequestCategory, User
from src.models.shelter import ShelterBeneficiary
from src.models.shelter import ShelterRequest
from src.schemas.ShelterRequestPayload import ShelterRequestPayload
from src.db.session import get_db

# ✅ Master Tables
from src.models.shelter import ShelterStayingTypes
from src.models.shelter import ShelterRequirementTypes
from src.models.shelter import ShelterSpecialNeeds
from src.models.shelter import ShelterDurationOptions
from src.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/api/v1/shelter",
    tags=["Shelter Categories"],
    # dependencies=[Depends(get_current_user_id)],
)

# ===========================
# ✅ MASTER GET APIs
# ===========================
@router.get("/staying-types", response_model=list[dict])
async def get_shelter_staying_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ShelterStayingTypes))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data] 

@router.get("/requirement-types", response_model=list[dict])
async def get_shelter_requirement_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ShelterRequirementTypes))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data]

@router.get("/special-needs", response_model=list[dict])
async def get_shelter_special_needs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ShelterSpecialNeeds))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data]

@router.get("/duration-options", response_model=list[dict])
async def get_shelter_duration_options(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ShelterDurationOptions))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data] 

# =========================
# ✅ POST
# =========================
@router.post("/shelter-request")
async def create_shelter_request(
    payload: ShelterRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:

        async def _exists(model, value: int):
            result = await db.execute(select(model.id).where(model.id == value))
            return result.scalar_one_or_none() is not None

        # ✅ Validate main
        if not await _exists(User, payload.user_id):
            raise HTTPException(400, "Invalid user_id")

        if not await _exists(RequestCategory, payload.category_id):
            raise HTTPException(400, "Invalid category_id")

        # ✅ Create request
        new_request = ShelterRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id,
            verified=payload.verified,
            reject_reason=payload.reject_reason,
            # amount_requested=payload.amount_requested
        )

        db.add(new_request)
        await db.flush()

        # ✅ Beneficiaries
        for i, ben in enumerate(payload.beneficiaries, start=1):

         # 🔥 ATTACHMENTS
            verification_id = None
            damage_id = None

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

            if ben.damage_document:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=ben.damage_document.document_type_id,
                    file_path=ben.damage_document.file_path
                )
                db.add(att)
                await db.flush()
                damage_id = att.id

            db.add(
                ShelterBeneficiary(
                    shelter_request_id=new_request.id,
                    person_name=ben.person_name,
                    total_members=ben.total_members,
                    special_need_id=ben.special_need_id,
                    staying_type_id=ben.staying_type_id,
                    current_address=ben.current_address,
                    duration_of_problem=ben.duration_of_problem,
                    requirement_type_id=ben.requirement_type_id,
                    duration_option_id=ben.duration_option_id,
                    number_of_days=ben.number_of_days,
                    verification_document_id=verification_id,
                    damage_document_id=damage_id,
                    amount_requested=payload.amount_requested
                )
            )

        await db.commit()

        return {"message": "Created successfully", "request_id": new_request.id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))
