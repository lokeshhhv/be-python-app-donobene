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

            # 🔥 VALIDATIONS
            if ben.special_need_id and not await _exists(ShelterSpecialNeeds, ben.special_need_id):
                raise HTTPException(400, f"Invalid special_need_id at beneficiaries[{i}]")

            if ben.staying_type_id and not await _exists(ShelterStayingTypes, ben.staying_type_id):
                raise HTTPException(400, f"Invalid staying_type_id at beneficiaries[{i}]")

            if ben.requirement_type_id and not await _exists(ShelterRequirementTypes, ben.requirement_type_id):
                raise HTTPException(400, f"Invalid requirement_type_id at beneficiaries[{i}]")

            if ben.duration_option_id and not await _exists(ShelterDurationOptions, ben.duration_option_id):
                raise HTTPException(400, f"Invalid duration_option_id at beneficiaries[{i}]")

            if ben.duration_option_id and not ben.number_of_days:
                raise HTTPException(400, "number_of_days required when duration_option_id is given")

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

# =========================
# ✅ GET
# =========================
# @router.get("/shelter-request")
# async def get_shelter_requests(user_id: int, db: AsyncSession = Depends(get_db)):

#     result = await db.execute(select(ShelterRequest).where(ShelterRequest.user_id == user_id))
#     requests = result.scalars().all()

#     response = []

#     for r in requests:

#         ben_result = await db.execute(
#             select(ShelterBeneficiary).where(
#                 ShelterBeneficiary.shelter_request_id == r.id
#             )
#         )
#         beneficiaries = ben_result.scalars().all()

#         ben_data = []

#         for b in beneficiaries:

#             verification_doc = None
#             damage_doc = None

#             if b.verification_document_id:
#                 res = await db.execute(select(Attachment).where(Attachment.id == b.verification_document_id))
#                 att = res.scalar_one_or_none()
#                 if att:
#                     verification_doc = {"id": att.id, "file_path": att.file_path}

#             if b.damage_document_id:
#                 res = await db.execute(select(Attachment).where(Attachment.id == b.damage_document_id))
#                 att = res.scalar_one_or_none()
#                 if att:
#                     damage_doc = {"id": att.id, "file_path": att.file_path}

#             ben_data.append({
#                 "id": b.id,
#                 "person_name": b.person_name,
#                 "total_members": b.total_members,
#                 "special_need_id": b.special_need_id,
#                 "staying_type_id": b.staying_type_id,
#                 "requirement_type_id": b.requirement_type_id,
#                 "duration_option_id": b.duration_option_id,
#                 "number_of_days": b.number_of_days,
#                 "verification_document": verification_doc,
#                 "damage_document": damage_doc
#             })

#         response.append({
#             "id": r.id,
#             "user_id": r.user_id,
#             "category_id": r.category_id,
#             "request_title": r.request_title,
#             "request_description": r.request_description,
#             "status_id": r.status_id,
#             "urgency_id": r.urgency_id,
#             "verified": r.verified,
#             "reject_reason": r.reject_reason,
#             "beneficiaries": ben_data
#         })

#     return response