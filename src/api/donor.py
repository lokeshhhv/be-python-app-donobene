# GET endpoint for clothes donations by user
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.types import Attachment, User
from src.models.donor import ClothesDonation, ClothesDonationDetail, DeliveryPreference, DonorAvailabilityType, DonorCategory, DonorClothesCategory, DonorClothesCondition, DonorClothesSize, DonorConsentType, DonorOrganDonation, DonorStemcellDonation, DonorTissueDonation, FoodDonation, FoodDonationDetail, MedicalDonation, MedicalDonationCategory, MedicalDonationCategory, MedicalDonationOrganMap, MedicalDonationStemcellMap, MedicalDonationTissueMap, Unit
from src.db.session import get_db
from src.schemas.donor import ClothesDonationCreate, DonorAvailabilityTypeSchema, DonorConsentTypeSchema, DonorOrganDonationSchema, DonorStemcellDonationSchema, DonorTissueDonationSchema, FoodDonationCreate, MedicalDonationCategorySchema, MedicalDonationCreate, MedicalDonationSchema
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
    prefix="/donor",
    tags=["donor"],
    # dependencies=[Depends(get_current_user_id)],
)

@router.post("/food-donation", response_model=dict)
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
            return error_response(message="Invalid user_id")

        if not await _exists(DonorCategory, payload.category_id):
            return error_response(message="Invalid category_id")

        if payload.delivery_preference_id and not await _exists(DeliveryPreference, payload.delivery_preference_id):
            return error_response(message="Invalid delivery_preference_id")

        for item in payload.items:
            if not await _exists(Unit, item.unit_id):
                return error_response(message=f"Invalid unit_id {item.unit_id}")

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
        return success_response(data={"donation_id": new_donation.id}, message="Food donation created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_food_donation: {e}")
        return error_response(message="An error occurred while creating the food donation", error=str(e))

@router.get("/donation-categories", response_model=dict)
async def get_food_donation_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorCategory))
        categories = result.scalars().all()
        return success_response(data=[{"id": cat.id, "category_id": cat.category_id, "category_type": cat.category_type, "backgroundColor": cat.backgroundColor, "icon": cat.icon} for cat in categories], message="Fetched donation categories")
    except Exception as e:
        logger.error(f"Error in get_food_donation_categories: {e}")
        return error_response(message="Failed to fetch donation categories", error=str(e))

@router.get("/food-donation-delivery-preferences", response_model=dict)
async def get_food_donation_delivery_preferences(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DeliveryPreference))
        preferences = result.scalars().all()
        return success_response(data=[{"id": pref.id, "name": pref.name} for pref in preferences], message="Fetched delivery preferences")
    except Exception as e:
        logger.error(f"Error in get_food_donation_delivery_preferences: {e}")
        return error_response(message="Failed to fetch delivery preferences", error=str(e))

@router.get("/food-donation-units", response_model=dict)
async def get_food_donation_units(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Unit))
        units = result.scalars().all()
        return success_response(data=[{"id": unit.id, "name": unit.name} for unit in units], message="Fetched food donation units")
    except Exception as e:
        logger.error(f"Error in get_food_donation_units: {e}")
        return error_response(message="Failed to fetch food donation units", error=str(e))

# Clothes donation endpoints would be similar to the above structure, with appropriate changes to models, schemas, and logic.

@router.get("/clothes-donation-categories", response_model=dict)
async def get_clothes_donation_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorClothesCategory))
        categories = result.scalars().all()
        return success_response(data=[{"id": cat.id, "name": cat.name} for cat in categories], message="Fetched clothes donation categories")
    except Exception as e:
        logger.error(f"Error in get_clothes_donation_categories: {e}")
        return error_response(message="Failed to fetch clothes donation categories", error=str(e))

@router.get("/clothes-donation-sizes", response_model=dict)
async def get_clothes_donation_sizes(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorClothesSize))
        sizes = result.scalars().all()
        return success_response(data=[{"id": size.id, "name": size.name} for size in sizes], message="Fetched clothes donation sizes")
    except Exception as e:
        logger.error(f"Error in get_clothes_donation_sizes: {e}")
        return error_response(message="Failed to fetch clothes donation sizes", error=str(e))

@router.get("/clothes-donation-conditions", response_model=dict)
async def get_clothes_donation_conditions(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorClothesCondition))
        conditions = result.scalars().all()
        return success_response(data=[{"id": condition.id, "name": condition.name} for condition in conditions], message="Fetched clothes donation conditions")
    except Exception as e:
        logger.error(f"Error in get_clothes_donation_conditions: {e}")
        return error_response(message="Failed to fetch clothes donation conditions", error=str(e))


@router.post("/clothes-donation", response_model=dict)
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
            return error_response(message="Invalid user_id")

        for detail in payload.details:
            if not await _exists(DonorClothesCategory, detail.category_id):
                return error_response(message=f"Invalid category_id {detail.category_id}")
            if not await _exists(DonorClothesSize, detail.size_id):
                return error_response(message=f"Invalid size_id {detail.size_id}")
            if not await _exists(DonorClothesCondition, detail.condition_id):
                return error_response(message=f"Invalid condition_id {detail.condition_id}")

        if payload.pickup_type_id and not await _exists(DeliveryPreference, payload.pickup_type_id):
            return error_response(message=f"Invalid pickup_type_id {payload.pickup_type_id}")

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
        return success_response(data={"donation_id": new_donation.id}, message="Clothes donation created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_clothes_donation: {e}")
        return error_response(message="An error occurred while creating the clothes donation", error=str(e))
    
# medical donation endpoints would be similar to the above structure, with appropriate changes to models, schemas, and logic.


@router.get("/medical-donation-categories", response_model=dict)
async def get_medical_donation_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(MedicalDonationCategory).where(MedicalDonationCategory.is_active == True))
        categories = result.scalars().all()
        # Cast size to string for response validation
        data = [
            MedicalDonationCategorySchema(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                icon=cat.icon,
                size=str(cat.size) if cat.size is not None else None,
                is_active=cat.is_active
            )
            for cat in categories
        ]
        return success_response(data=data, message="Fetched medical donation categories")
    except Exception as e:
        logger.error(f"Error in get_medical_donation_categories: {e}")
        return error_response(message="Failed to fetch medical donation categories", error=str(e))


@router.get("/stemcell-donations", response_model=dict)
async def get_stemcell_donations(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorStemcellDonation))
        donations = result.scalars().all()
        return success_response(
            data=[{"id": d.id, "name": d.name} for d in donations],
            message="Fetched stemcell donations"
        )
    except Exception as e:
        logger.error(f"Error in get_stemcell_donations: {e}")
        return error_response(message="Failed to fetch stemcell donations", error=str(e))

@router.get("/tissue-donations", response_model=dict)
async def get_tissue_donations(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorTissueDonation))
        donations = result.scalars().all()
        return success_response(
            data=[{"id": d.id, "name": d.name} for d in donations],
            message="Fetched tissue donations"
        )
    except Exception as e:
        logger.error(f"Error in get_tissue_donations: {e}")
        return error_response(message="Failed to fetch tissue donations", error=str(e))

@router.get("/organ-donations", response_model=dict)
async def get_organ_donations(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorOrganDonation))
        donations = result.scalars().all()
        return success_response(
            data=[{"id": d.id, "name": d.name} for d in donations],
            message="Fetched organ donations"
        )
    except Exception as e:
        logger.error(f"Error in get_organ_donations: {e}")
        return error_response(message="Failed to fetch organ donations", error=str(e))

@router.get("/consent-types", response_model=dict)
async def get_consent_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorConsentType))
        consent_types = result.scalars().all()
        return success_response(
            data=[{"id": c.id, "name": c.name} for c in consent_types],
            message="Fetched consent types"
        )
    except Exception as e:
        logger.error(f"Error in get_consent_types: {e}")
        return error_response(message="Failed to fetch consent types", error=str(e))

@router.get("/availability-types", response_model=dict)
async def get_availability_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DonorAvailabilityType))
        availability_types = result.scalars().all()
        return success_response(
            data=[{"id": a.id, "name": a.name} for a in availability_types],
            message="Fetched availability types"
        )
    except Exception as e:
        logger.error(f"Error in get_availability_types: {e}")
        return error_response(message="Failed to fetch availability types", error=str(e))

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
    

# my donations endpoint to fetch all donations by a user across categories (clothes, food, medical)

@router.get("/my-donations/{user_id}")
async def get_my_donations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Fetch all related data for mapping ids to names
        categories = {c.id: c for c in (await db.execute(select(DonorCategory))).scalars().all()}
        clothes_categories = {c.id: c for c in (await db.execute(select(DonorClothesCategory))).scalars().all()}
        clothes_sizes = {s.id: s for s in (await db.execute(select(DonorClothesSize))).scalars().all()}
        clothes_conditions = {c.id: c for c in (await db.execute(select(DonorClothesCondition))).scalars().all()}
        delivery_prefs = {d.id: d for d in (await db.execute(select(DeliveryPreference))).scalars().all()}
        units = {u.id: u for u in (await db.execute(select(Unit))).scalars().all()}
        med_categories = {c.id: c for c in (await db.execute(select(MedicalDonationCategory))).scalars().all()}
        avail_types = {a.id: a for a in (await db.execute(select(DonorAvailabilityType))).scalars().all()}
        consent_types = {c.id: c for c in (await db.execute(select(DonorConsentType))).scalars().all()}
        organ_map = {o.id: o for o in (await db.execute(select(DonorOrganDonation))).scalars().all()}
        tissue_map = {t.id: t for t in (await db.execute(select(DonorTissueDonation))).scalars().all()}
        stemcell_map = {s.id: s for s in (await db.execute(select(DonorStemcellDonation))).scalars().all()}
        # Gender and BloodGroup
        from src.models.types import Gender
        from src.models.medical import BloodGroup
        genders = {g.id: g for g in (await db.execute(select(Gender))).scalars().all()}
        blood_groups = {b.id: b for b in (await db.execute(select(BloodGroup))).scalars().all()}
        # Fetch all attachments for clothes and food donations
        from src.models.types import Attachment
        clothes_attachments = {a.request_id: a for a in (await db.execute(select(Attachment))).scalars().all() if a.category_id in clothes_categories}
        food_attachments = {a.request_id: a for a in (await db.execute(select(Attachment))).scalars().all() if a.category_id in categories}

        # Fetch clothes donations
        clothes_result = await db.execute(select(ClothesDonation).where(ClothesDonation.user_id == user_id))
        clothes_donations = []
        for c in clothes_result.scalars().all():
            # Fetch details for each clothes donation
            details_result = await db.execute(select(ClothesDonationDetail).where(ClothesDonationDetail.clothes_donation_id == c.id))
            details = []
            for d in details_result.scalars().all():
                details.append({
                    "category": clothes_categories.get(d.category_id).name if d.category_id in clothes_categories else None,
                    "size": clothes_sizes.get(d.size_id).name if d.size_id in clothes_sizes else None,
                    "condition": clothes_conditions.get(d.condition_id).name if d.condition_id in clothes_conditions else None,
                    "quantity": d.quantity
                })
            # Fetch attachment for this clothes donation
            attachment = None
            if c.verification_image_id:
                att = clothes_attachments.get(c.id)
                if att:
                    attachment = {
                        "id": att.id,
                        "file_path": att.file_path,
                        "document_type_id": att.document_type_id
                    }
            clothes_donations.append({
                "id": c.id,
                "description": c.description,
                "category": categories.get(c.category_id).category_type if c.category_id in categories else None,
                "pickup_type": delivery_prefs.get(c.pickup_type_id).name if c.pickup_type_id in delivery_prefs else None,
                "available_date": c.available_date,
                "notes": c.notes,
                "details": details,
                "attachment": attachment
            })

        # Fetch food donations
        food_result = await db.execute(select(FoodDonation).where(FoodDonation.user_id == user_id))
        food_donations = []
        for f in food_result.scalars().all():
            # Fetch details for each food donation
            details_result = await db.execute(select(FoodDonationDetail).where(FoodDonationDetail.food_donation_id == f.id))
            details = []
            for d in details_result.scalars().all():
                details.append({
                    "items": d.items,
                    "quantity": d.quantity,
                    "unit": units.get(d.unit_id).name if d.unit_id in units else None
                })
            # Fetch attachment for this food donation
            attachment = None
            if f.verification_document_id:
                att = food_attachments.get(f.id)
                if att:
                    attachment = {
                        "id": att.id,
                        "file_path": att.file_path,
                        "document_type_id": att.document_type_id
                    }
            food_donations.append({
                "id": f.id,
                "donation_title": f.donation_title,
                "category": categories.get(f.category_id).category_type if f.category_id in categories else None,
                "delivery_preference": delivery_prefs.get(f.delivery_preference_id).name if f.delivery_preference_id in delivery_prefs else None,
                "preferred_date": f.preferred_date,
                "notes": f.notes,
                "details": details,
                "attachment": attachment
            })

        # Fetch medical donations
        medical_result = await db.execute(select(MedicalDonation).where(MedicalDonation.user_id == user_id))
        medical_donations = []
        for m in medical_result.scalars().all():
            # Fetch organ, tissue, stemcell mappings
            organ_ids = [o.donor_organ_donation_id for o in (await db.execute(select(MedicalDonationOrganMap).where(MedicalDonationOrganMap.medical_donation_id == m.id))).scalars().all()]
            tissue_ids = [t.donor_tissue_donation_id for t in (await db.execute(select(MedicalDonationTissueMap).where(MedicalDonationTissueMap.medical_donation_id == m.id))).scalars().all()]
            stemcell_ids = [s.donor_stemcell_donation_id for s in (await db.execute(select(MedicalDonationStemcellMap).where(MedicalDonationStemcellMap.medical_donation_id == m.id))).scalars().all()]
            medical_donations.append({
                "id": m.id,
                "full_name": m.full_name,
                "category": categories.get(m.category_id).category_type if m.category_id in categories else None,
                "medical_donation_category": med_categories.get(m.medical_donation_category_id).name if m.medical_donation_category_id in med_categories else None,
                "age_group": m.age_group,
                "gender": genders.get(m.gender_id).gender_name if m.gender_id in genders else None,
                "contact_number": m.contact_number,
                "blood_group": blood_groups.get(m.blood_group_id).name if m.blood_group_id in blood_groups else None,
                "milk_volume": m.milk_volume,
                "baby_age_months": m.baby_age_months,
                "supply_type": m.supply_type,
                "quantity": m.quantity,
                "weight_kg": float(m.weight_kg) if m.weight_kg is not None else None,
                "major_illness": m.major_illness,
                "recent_surgery": m.recent_surgery,
                "last_donation_date": m.last_donation_date,
                "currently_on_medication": m.currently_on_medication,
                "donation_type": m.donation_type,
                "availability_type": avail_types.get(m.availability_type_id).name if m.availability_type_id in avail_types else None,
                "consent_type": consent_types.get(m.consent_type_id).name if m.consent_type_id in consent_types else None,
                "preferred_hospital": m.preferred_hospital,
                "donation_location": m.donation_location,
                "organs": [organ_map.get(oid).name for oid in organ_ids if oid in organ_map],
                "tissues": [tissue_map.get(tid).name for tid in tissue_ids if tid in tissue_map],
                "stemcells": [stemcell_map.get(sid).name for sid in stemcell_ids if sid in stemcell_map]
            })

        return success_response(data={
            "clothes_donations": clothes_donations,
            "food_donations": food_donations,
            "medical_donations": medical_donations,
        }, message="Fetched all donations successfully")
    except Exception as e:
        logger.error(f"Error in get_my_donations: {e}")
        return error_response(message="Error fetching donations", error=str(e))