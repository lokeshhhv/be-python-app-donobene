from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.types import User
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
from src.models.sports import (
    SportsRequestBeneficiarySupportType,
)
from src.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Sports Categories"],
    dependencies=[Depends(get_current_user_id)],
)

# ===========================
# ✅ MASTER GET APIs
# ===========================

@router.get("/sports-categories", response_model=list[dict])
async def get_sports_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SportsCategory))
    data = result.scalars().all()
    return [{"id": d.id, "name": d.name} for d in data]


@router.get("/sports-support-types", response_model=list[dict])
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

@router.post("/sports-request", response_model=dict)
async def create_sports_request(
    payload: SportsRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Validate top-level foreign keys before insert to return clear API errors.
        async def _exists(model, value: int) -> bool:
            result = await db.execute(select(model.id).where(model.id == value))
            return result.scalar_one_or_none() is not None

        if not await _exists(User, payload.user_id):
            raise HTTPException(status_code=400, detail=f"Invalid user_id: {payload.user_id}")

        if not await _exists(RequestCategory, payload.category_id):
            raise HTTPException(status_code=400, detail=f"Invalid category_id: {payload.category_id}")

        for index, ben in enumerate(payload.beneficiaries, start=1):
            if ben.gender_id is not None and not await _exists(Gender, ben.gender_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid gender_id at beneficiaries[{index}]: {ben.gender_id}",
                )

            if not await _exists(PlayingLevel, ben.playing_level_id):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid playing_level_id at beneficiaries[{index}]: "
                        f"{ben.playing_level_id}"
                    ),
                )

            if not await _exists(SportsCategory, ben.sports_category_id):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid sports_category_id at beneficiaries[{index}]: "
                        f"{ben.sports_category_id}"
                    ),
                )

            for sup_index, support in enumerate(ben.support_types, start=1):
                if not await _exists(SportsSupportType, support.support_type_id):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Invalid support_type_id at beneficiaries[{index}]"
                            f".support_types[{sup_index}]: {support.support_type_id}"
                        ),
                    )

        # 1️⃣ Create main request
        new_request = SportsRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description
        )
        db.add(new_request)
        await db.flush()

        # 2️⃣ Beneficiaries
        for ben in payload.beneficiaries:
            new_ben = SportsRequestBeneficiary(
                sports_request_id=new_request.id,
                person_name=ben.person_name,
                age_group=ben.age_group,
                gender_id=ben.gender_id,
                playing_level_id=ben.playing_level_id,
                achievement=ben.achievement,
                sports_category_id=ben.sports_category_id,
                amount_requested=ben.amount_requested,
                event_date=ben.event_date,
                institution_name=ben.institution_name,
                phone=ben.phone,
                verification_document_id=ben.verification_document_id,
                achievement_document_id=ben.achievement_document_id
            )
            db.add(new_ben)
            await db.flush()

            # 3️⃣ Support types
            for s in ben.support_types:
                db.add(
                    SportsRequestBeneficiarySupportType(
                        beneficiary_id=new_ben.id,
                        support_type_id=s.support_type_id
                    )
                )

        await db.commit()

        return {
            "message": "Sports request created successfully",
            "request_id": new_request.id
        }

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid foreign key reference in sports request payload",
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# ✅ GET API (LIST)
# ===========================

@router.get("/sports-request", response_model=list[dict])
async def get_sports_requests(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(SportsRequest)

    if user_id:
        query = query.where(SportsRequest.user_id == user_id)

    result = await db.execute(query)
    requests = result.scalars().all()

    response = []

    for r in requests:
        ben_result = await db.execute(
            select(SportsRequestBeneficiary).where(
                SportsRequestBeneficiary.sports_request_id == r.id
            )
        )
        beneficiaries = ben_result.scalars().all()

        ben_data = []

        for b in beneficiaries:
            sup_result = await db.execute(
                select(SportsRequestBeneficiarySupportType).where(
                    SportsRequestBeneficiarySupportType.beneficiary_id == b.id
                )
            )
            supports = sup_result.scalars().all()

            ben_data.append({
                "id": b.id,
                "person_name": b.person_name,
                "age_group": b.age_group,
                "gender_id": b.gender_id,
                "playing_level_id": b.playing_level_id,
                "sports_category_id": b.sports_category_id,
                "achievement": b.achievement,
                "amount_requested": float(b.amount_requested) if b.amount_requested else None,
                "event_date": b.event_date,
                "institution_name": b.institution_name,
                "phone": b.phone,
                "verification_document_id": b.verification_document_id,
                "achievement_document_id": b.achievement_document_id,
                "support_types": [
                    {"support_type_id": s.support_type_id}
                    for s in supports
                ]
            })

        response.append({
            "id": r.id,
            "user_id": r.user_id,
            "category_id": r.category_id,
            "request_title": r.request_title,
            "request_description": r.request_description,
            "beneficiaries": ben_data
        })

    return response