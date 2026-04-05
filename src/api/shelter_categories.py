from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
    prefix="/api/v1/shelter-categories",
    tags=["Shelter Categories"],
    dependencies=[Depends(get_current_user_id)],
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
@router.post("/shelter-request", response_model=dict)
async def create_shelter_request(
    payload: ShelterRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1️⃣ Main request
        new_request = ShelterRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id
        )
        db.add(new_request)
        await db.flush()

        # 2️⃣ Beneficiaries
        for ben in payload.beneficiaries:
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
                    verification_document_id=ben.verification_document_id,
                    damage_document_id=ben.damage_document_id
                )
            )

        await db.commit()

        return {
            "message": "Shelter request created successfully",
            "request_id": new_request.id
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# ✅ GET
# =========================
@router.get("/shelter-request", response_model=list[dict])
async def get_shelter_requests(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(ShelterRequest)

    if user_id:
        query = query.where(ShelterRequest.user_id == user_id)

    result = await db.execute(query)
    requests = result.scalars().all()

    response = []

    for r in requests:
        ben_result = await db.execute(
            select(ShelterBeneficiary).where(
                ShelterBeneficiary.shelter_request_id == r.id
            )
        )
        beneficiaries = ben_result.scalars().all()

        ben_data = [
            {
                "id": b.id,
                "person_name": b.person_name,
                "total_members": b.total_members,
                "special_need_id": b.special_need_id,
                "staying_type_id": b.staying_type_id,
                "requirement_type_id": b.requirement_type_id,
                "duration_option_id": b.duration_option_id,
                "number_of_days": b.number_of_days,
                "verification_document_id": b.verification_document_id,
                "damage_document_id": b.damage_document_id
            }
            for b in beneficiaries
        ]

        response.append({
            "id": r.id,
            "user_id": r.user_id,
            "category_id": r.category_id,
            "request_title": r.request_title,
            "request_description": r.request_description,
            "status_id": r.status_id,
            "urgency_id": r.urgency_id,
            "beneficiaries": ben_data
        })

    return response