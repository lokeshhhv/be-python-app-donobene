from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from src.schemas.ClothesRequestPayload import ClothesRequestPayload
from src.models.clothes import ClothesRequest, ClothesRequestBeneficiaries, ClothesRequestBeneficiariesSizes
from src.models.clothes import ClothingSizeRow
from src.models.clothes import ClothingCategory
from src.models.clothes import ClothesAgeGroup
from src.models.types import Attachment, RequestCategory


from src.db.session import get_db
from src.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Clothes Categories"],
    dependencies=[Depends(get_current_user_id)],
)

@router.get("/request-categories", response_model=list[dict])
async def get_request_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RequestCategory))
    request_categories = result.scalars().all()
    return [
        {"id": rc.id, "category_id": rc.category_id, "category_type": rc.category_type} for rc in request_categories
    ]

@router.get("/clothes-age-groups", response_model=list[dict])
async def get_clothes_age_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClothesAgeGroup))
    clothes_age_groups = result.scalars().all()
    return [
        {"id": cag.id, "name": cag.name} for cag in clothes_age_groups
    ]

@router.get("/clothing-categories", response_model=list[dict])
async def get_clothing_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClothingCategory))
    clothing_categories = result.scalars().all()
    return [
        {"id": cc.id, "name": cc.name} for cc in clothing_categories
    ]

@router.get("/clothing-size-rows", response_model=list[dict])
async def get_clothing_size_rows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClothingSizeRow))
    clothing_size_rows = result.scalars().all()
    return [
        {"id": csr.id, "name": csr.name} for csr in clothing_size_rows
    ]

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
            urgency_id=payload.urgency_id
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
                beneficiary_photo_id=beneficiary_photo_id
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

        return {"message": "Clothes request created successfully", "request_id": new_request.id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/clothes-request", response_model=list[dict])
async def get_clothes_requests(user_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    query = select(ClothesRequest)
    if user_id:
        query = query.where(ClothesRequest.user_id == user_id)

    result = await db.execute(query)
    requests = result.scalars().all()
    response_data = []

    for r in requests:
        ben_result = await db.execute(
            select(ClothesRequestBeneficiaries).where(
                ClothesRequestBeneficiaries.clothes_request_id == r.id
            )
        )
        beneficiaries = ben_result.scalars().all()
        ben_list = []

        for ben in beneficiaries:
            size_result = await db.execute(
                select(ClothesRequestBeneficiariesSizes).where(
                    ClothesRequestBeneficiariesSizes.beneficiary_id == ben.id
                )
            )
            sizes = size_result.scalars().all()


            # Fetch verification_document and beneficiary_photo as objects (id and file_path)
            verification_doc = None
            beneficiary_photo = None

            if ben.verification_document_id:
                res = await db.execute(select(Attachment).where(Attachment.id == ben.verification_document_id))
                att = res.scalar_one_or_none()
                if att:
                    verification_doc = {"id": att.id, "file_path": att.file_path}

            if ben.beneficiary_photo_id:
                res = await db.execute(select(Attachment).where(Attachment.id == ben.beneficiary_photo_id))
                att = res.scalar_one_or_none()
                if att:
                    beneficiary_photo = {"id": att.id, "file_path": att.file_path}

            ben_list.append({
                "id": ben.id,
                "person_name": ben.person_name,
                "age_group": ben.age_group,
                "gender_preference": ben.gender_preference,
                "clothing_category_id": ben.clothing_category_id,
                "need_by_date": ben.need_by_date,
                "urgency_level_id": ben.urgency_level_id,
                "verification_document": verification_doc,
                "beneficiary_photo": beneficiary_photo,
                "sizes": [
                    {
                        "id": s.id,
                        "clothing_type": s.clothing_type,
                        "size_id": s.size_id,
                        "quantity": s.quantity
                    }
                    for s in sizes
                ]
            })

        response_data.append({
            "id": r.id,
            "user_id": r.user_id,
            "category_id": r.category_id,
            "request_title": r.request_title,
            "request_description": r.request_description,
            "status_id": r.status_id,
            "urgency_id": r.urgency_id,
            "beneficiaries": ben_list
        })

    return response_data