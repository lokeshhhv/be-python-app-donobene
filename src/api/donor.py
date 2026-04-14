# GET endpoint for clothes donations by user
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.types import Attachment, User
from src.models.donor import ClothesDonation, ClothesDonationDetail, DeliveryPreference, DonorAvailabilityType, DonorCategory, DonorClothesCategory, DonorClothesCondition, DonorClothesSize, DonorConsentType, DonorOrganDonation, DonorStemcellDonation, DonorTissueDonation, FoodDonation, FoodDonationDetail, MedicalDonation, MedicalDonationCategory, MedicalDonationCategory, MedicalDonationOrganMap, MedicalDonationStemcellMap, MedicalDonationTissueMap, Unit
from src.db.session import get_db
from src.schemas.donor import ClothesDonationCreate, DonorAvailabilityTypeSchema, DonorConsentTypeSchema, DonorOrganDonationSchema, DonorStemcellDonationSchema, DonorTissueDonationSchema, FoodDonationCreate, MedicalDonationCategorySchema, MedicalDonationCreate, MedicalDonationSchema
from src.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/donor",
    tags=["donor"],
    # dependencies=[Depends(get_current_user_id)],
)

@router.post("/food-donation")
async def create_food_donation(
    payload: FoodDonationCreate,
    db: AsyncSession = Depends(get_db)
):
    try:

        async def _exists(model, value: int):
            result = await db.execute(select(model.id).where(model.id == value))
            return result.scalar_one_or_none() is not None

        # ✅ validate
        if not await _exists(User, payload.user_id):
            raise HTTPException(400, "Invalid user_id")

        if not await _exists(DonorCategory, payload.category_id):
            raise HTTPException(400, "Invalid category_id")

        if payload.delivery_preference_id and not await _exists(DeliveryPreference, payload.delivery_preference_id):
            raise HTTPException(400, "Invalid delivery_preference_id")

        for item in payload.items:
            if not await _exists(Unit, item.unit_id):
                raise HTTPException(400, f"Invalid unit_id {item.unit_id}")
            
        # ✅ create donation
        new_donation = FoodDonation(
            user_id=payload.user_id,
            category_id=payload.category_id,
            donation_title=payload.donation_title,
            delivery_preference_id=payload.delivery_preference_id,
            preferred_date=payload.preferred_date,
            notes=payload.notes,
            verification_document_id=None
        )
        db.add(new_donation)
        await db.commit()
        await db.refresh(new_donation)

        # ✅ create attachment if present
        if payload.verification_document:
            att = Attachment(
                user_id=payload.user_id,
                request_id=new_donation.id,
                category_id=payload.category_id,
                document_type_id=payload.verification_document.document_type_id,
                file_path=payload.verification_document.file_path
            )
            db.add(att)
            await db.commit()
            await db.refresh(att)
            # update donation with attachment id
            new_donation.verification_document_id = att.id
            db.add(new_donation)
            await db.commit()
            await db.refresh(new_donation)
        db.add(new_donation)
        await db.commit()
        await db.refresh(new_donation)

        # ✅ create donation details
        for item in payload.items:
            donation_detail = FoodDonationDetail(
                food_donation_id=new_donation.id,
                items=item.items,
                quantity=item.quantity,
                unit_id=item.unit_id
            )
            db.add(donation_detail)

        await db.commit()

        return {"message": "Food donation created successfully", "donation_id": new_donation.id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"An error occurred while creating the food donation: {str(e)}")
    
@router.get("/food-donation/{user_id}", response_model=list[dict])
async def get_food_donations(user_id: int, db: AsyncSession = Depends(get_db)):
    try:

        # ✅ get all donations
        result = await db.execute(select(FoodDonation).where(FoodDonation.user_id == user_id))
        donations = result.scalars().all()

        # Batch fetch related data for all donations
        category_ids = {d.category_id for d in donations}
        delivery_pref_ids = {d.delivery_preference_id for d in donations if d.delivery_preference_id}
        verification_doc_ids = {d.verification_image_id for d in donations if d.verification_image_id}
        donation_ids = [d.id for d in donations]

        # Fetch all related categories
        categories = (await db.execute(select(DonorCategory).where(DonorCategory.id.in_(category_ids)))).scalars().all()
        category_map = {c.id: c for c in categories}

        # Fetch all related delivery preferences
        delivery_prefs = (await db.execute(select(DeliveryPreference).where(DeliveryPreference.id.in_(delivery_pref_ids)))).scalars().all()
        delivery_pref_map = {d.id: d for d in delivery_prefs}

        # Fetch all related attachments
        attachments = (await db.execute(select(Attachment).where(Attachment.id.in_(verification_doc_ids)))).scalars().all()
        attachment_map = {a.id: a for a in attachments}

        # Fetch all child items for all donations
        all_items = (await db.execute(select(FoodDonationDetail).where(FoodDonationDetail.food_donation_id.in_(donation_ids)))).scalars().all()
        # Fetch all units for all items
        unit_ids = {item.unit_id for item in all_items}
        units = (await db.execute(select(Unit).where(Unit.id.in_(unit_ids)))).scalars().all()
        unit_map = {u.id: u for u in units}

        # Group items by donation id
        from collections import defaultdict
        items_by_donation = defaultdict(list)
        for item in all_items:
            items_by_donation[item.food_donation_id].append(item)

        response = []
        for donation in donations:
            item_dicts = []
            for item in items_by_donation[donation.id]:
                unit = unit_map.get(item.unit_id)
                item_dicts.append({
                    "id": item.id,
                    "food_donation_id": item.food_donation_id,
                    "items": item.items,
                    "quantity": item.quantity,
                    "unit_name": unit.name if unit else None
                })

            response.append({
                "id": donation.id,
                "user_id": donation.user_id,
                "category_name": category_map.get(donation.category_id).category_type if category_map.get(donation.category_id) else None,
                "donation_title": donation.donation_title,
                "delivery_preference_name": delivery_pref_map.get(donation.delivery_preference_id).name if delivery_pref_map.get(donation.delivery_preference_id) else None,
                "preferred_date": donation.preferred_date,
                "verification_document_file_path": (
                    attachment_map.get(donation.verification_image_id).file_path
                    if donation.verification_image_id and attachment_map.get(donation.verification_image_id) else None
                ),
                "notes": donation.notes,
                "created_at": donation.created_at,
                "updated_at": donation.updated_at,
                "items": item_dicts
            })
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching food donations: {str(e)}"
        )

@router.get("/food-donation-categories", response_model=list[dict])
async def get_food_donation_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorCategory))
    categories = result.scalars().all()
    return [
        {"id": cat.id, "category_id": cat.category_id, "category_type": cat.category_type} for cat in categories
    ]

@router.get("/food-donation-delivery-preferences", response_model=list[dict])
async def get_food_donation_delivery_preferences(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DeliveryPreference))
    preferences = result.scalars().all()
    return [
        {"id": pref.id, "name": pref.name} for pref in preferences
    ]

@router.get("/food-donation-units", response_model=list[dict])
async def get_food_donation_units(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Unit))
    units = result.scalars().all()
    return [
        {"id": unit.id, "name": unit.name} for unit in units
    ]

# Clothes donation endpoints would be similar to the above structure, with appropriate changes to models, schemas, and logic.

@router.get("/clothes-donation-categories", response_model=list[dict])
async def get_clothes_donation_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorClothesCategory))
    categories = result.scalars().all()
    return [
        {"id": cat.id, "name": cat.name} for cat in categories
    ]

@router.get("/clothes-donation-sizes", response_model=list[dict])
async def get_clothes_donation_sizes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorClothesSize))
    sizes = result.scalars().all()
    return [
        {"id": size.id, "name": size.name} for size in sizes
    ]

@router.get("/clothes-donation-conditions", response_model=list[dict])
async def get_clothes_donation_conditions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorClothesCondition))
    conditions = result.scalars().all()
    return [
        {"id": condition.id, "name": condition.name} for condition in conditions
    ]


@router.post("/clothes-donation")
async def create_clothes_donation(
    payload: ClothesDonationCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        async def _exists(model, value: int):
            result = await db.execute(select(model.id).where(model.id == value))
            return result.scalar_one_or_none() is not None

        # ✅ validate
        if not await _exists(User, payload.user_id):
            raise HTTPException(400, "Invalid user_id")

        for detail in payload.details:
            if not await _exists(DonorClothesCategory, detail.category_id):
                raise HTTPException(400, f"Invalid category_id {detail.category_id}")
            if not await _exists(DonorClothesSize, detail.size_id):
                raise HTTPException(400, f"Invalid size_id {detail.size_id}")
            if not await _exists(DonorClothesCondition, detail.condition_id):
                raise HTTPException(400, f"Invalid condition_id {detail.condition_id}")

        if payload.pickup_type_id and not await _exists(DeliveryPreference, payload.pickup_type_id):
            raise HTTPException(400, f"Invalid pickup_type_id {payload.pickup_type_id}")

        # ✅ create donation
        new_donation = ClothesDonation(
            user_id=payload.user_id,
            description=payload.description,
            category_id=payload.category_id,
            pickup_type_id=payload.pickup_type_id,
            available_date=payload.available_date,
            verification_image_id=None,
            notes=payload.notes
        )
        db.add(new_donation)
        await db.commit()
        await db.refresh(new_donation)

        # ✅ create attachment if present
        if payload.verification_document:
            att = Attachment(
                user_id=payload.user_id,
                request_id=new_donation.id,
                category_id=payload.category_id,  # Set category for clothes
                document_type_id=payload.verification_document.document_type_id,
                file_path=payload.verification_document.file_path
            )
            db.add(att)
            await db.commit()
            await db.refresh(att)
            # update donation with attachment id
            new_donation.verification_image_id = att.id
            db.add(new_donation)
            await db.commit()
            await db.refresh(new_donation)

        # ✅ create donation details
        for detail in payload.details:
            donation_detail = ClothesDonationDetail(
                clothes_donation_id=new_donation.id,
                category_id=detail.category_id,
                size_id=detail.size_id,
                condition_id=detail.condition_id,
                quantity=detail.quantity
            )
            db.add(donation_detail)

        await db.commit()

        return {"message": "Clothes donation created successfully", "donation_id": new_donation.id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"An error occurred while creating the clothes donation: {str(e)}")

@router.get("/clothes-donation/{user_id}", response_model=list[dict])
async def get_clothes_donations(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # ✅ get all donations
        result = await db.execute(select(ClothesDonation).where(ClothesDonation.user_id == user_id))
        donations = result.scalars().all()

        # Batch fetch related data for all donations
        pickup_type_ids = {d.pickup_type_id for d in donations if d.pickup_type_id}
        verification_doc_ids = {d.verification_image_id for d in donations if d.verification_image_id}
        donation_ids = [d.id for d in donations]

        # Fetch all related delivery preferences
        delivery_prefs = (await db.execute(select(DeliveryPreference).where(DeliveryPreference.id.in_(pickup_type_ids)))).scalars().all()
        delivery_pref_map = {d.id: d for d in delivery_prefs}

        # Fetch all related attachments
        attachments = (await db.execute(select(Attachment).where(Attachment.id.in_(verification_doc_ids)))).scalars().all()
        attachment_map = {a.id: a for a in attachments}

        # Fetch all child items for all donations
        all_items = (await db.execute(select(ClothesDonationDetail).where(ClothesDonationDetail.clothes_donation_id.in_(donation_ids)))).scalars().all()
        # Fetch all categories, sizes, and conditions for all items
        category_ids = {item.category_id for item in all_items}
        size_ids = {item.size_id for item in all_items}
        condition_ids = {item.condition_id for item in all_items}

        categories = (await db.execute(select(DonorClothesCategory).where(DonorClothesCategory.id.in_(category_ids)))).scalars().all()
        category_map = {c.id: c for c in categories}
        sizes = (await db.execute(select(DonorClothesSize).where(DonorClothesSize.id.in_(size_ids)))).scalars().all()
        size_map = {s.id: s for s in sizes}
        conditions = (await db.execute(select(DonorClothesCondition).where(DonorClothesCondition.id.in_(condition_ids)))).scalars().all()
        condition_map = {c.id: c for c in conditions}

        # Group items by donation id
        from collections import defaultdict
        items_by_donation = defaultdict(list)
        for item in all_items:
            items_by_donation[item.clothes_donation_id].append(item)

        response = []
        for donation in donations:
            item_dicts = []
            for item in items_by_donation[donation.id]:
                item_dicts.append({
                    "id": item.id,
                    "clothes_donation_id": item.clothes_donation_id,
                    "category_name": category_map.get(item.category_id).name if category_map.get(item.category_id) else None,
                    "size_name": size_map.get(item.size_id).name if size_map.get(item.size_id) else None,
                    "condition_name": condition_map.get(item.condition_id).name if condition_map.get(item.condition_id) else None,
                    "quantity": item.quantity
                })

            response.append({
                "id": donation.id,
                "user_id": donation.user_id,
                "description": donation.description,
                "pickup_type_name": delivery_pref_map.get(donation.pickup_type_id).name if delivery_pref_map.get(donation.pickup_type_id) else None,
                "available_date": donation.available_date,
                "verification_document_file_path": (
                    attachment_map.get(donation.verification_image_id).file_path
                    if donation.verification_image_id and attachment_map.get(donation.verification_image_id) else None
                ),
                "notes": donation.notes,
                "created_at": donation.created_at,
                "updated_at": donation.updated_at,
                "items": item_dicts
            })
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching clothes donations: {str(e)}"
        )
    
# medical donation endpoints would be similar to the above structure, with appropriate changes to models, schemas, and logic.


@router.get("/medical-donation-categories", response_model=list[MedicalDonationCategorySchema])
async def get_medical_donation_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MedicalDonationCategory).where(MedicalDonationCategory.is_active == True))
    categories = result.scalars().all()
    return categories


@router.get("/stemcell-donations", response_model=list[DonorStemcellDonationSchema])
async def get_stemcell_donations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorStemcellDonation))
    donations = result.scalars().all()
    return donations

@router.get("/tissue-donations", response_model=list[DonorTissueDonationSchema])
async def get_tissue_donations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorTissueDonation))
    return result.scalars().all()

@router.get("/organ-donations", response_model=list[DonorOrganDonationSchema])
async def get_organ_donations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorOrganDonation))
    return result.scalars().all()

@router.get("/consent-types", response_model=list[DonorConsentTypeSchema])
async def get_consent_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorConsentType))
    return result.scalars().all()

@router.get("/availability-types", response_model=list[DonorAvailabilityTypeSchema])
async def get_availability_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DonorAvailabilityType))
    return result.scalars().all()

@router.post("/medical-donations")
async def create_medical_donation(payload: MedicalDonationCreate, db: AsyncSession = Depends(get_db)):
    try:
        donation = MedicalDonation(
            user_id=payload.user_id,
            category_id=payload.category_id,
            medical_donation_category_id=payload.medical_donation_category_id,
            full_name=payload.full_name,
            age_group=payload.age_group,
            gender_id=payload.gender_id,
            contact_number=payload.contact_number,
            blood_group_id=payload.blood_group_id,
            milk_volume=payload.milk_volume,
            baby_age_months=payload.baby_age_months,
            supply_type=payload.supply_type,
            quantity=payload.quantity,
            weight_kg=payload.weight_kg,
            major_illness=payload.major_illness,
            recent_surgery=payload.recent_surgery,
            last_donation_date=payload.last_donation_date,
            currently_on_medication=payload.currently_on_medication,
            donation_type=payload.donation_type,
            availability_type_id=payload.availability_type_id,
            consent_type_id=payload.consent_type_id,
            preferred_hospital=payload.preferred_hospital,
            donation_location=payload.donation_location
        )
        db.add(donation)
        await db.commit()
        await db.refresh(donation)

        # Add mapping table entries
        for organ_id in payload.organ_ids or []:
            db.add(MedicalDonationOrganMap(medical_donation_id=donation.id, donor_organ_donation_id=organ_id))
        for tissue_id in payload.tissue_ids or []:
            db.add(MedicalDonationTissueMap(medical_donation_id=donation.id, donor_tissue_donation_id=tissue_id))
        for stemcell_id in payload.stemcell_ids or []:
            db.add(MedicalDonationStemcellMap(medical_donation_id=donation.id, donor_stemcell_donation_id=stemcell_id))
        await db.commit()

        return {"message": "Medical donation created successfully", "donation_id": donation.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Error creating medical donation: {str(e)}")