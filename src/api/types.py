
from typing import Optional, Any


from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from src.schemas.types import AttachmentResponse, UserProfileResponse
from src.schemas.ShelterRequestPayload import ShelterRequestPayload, ShelterBeneficiaryPayload
from src.schemas.SportsRequestPayload import SportsRequestPayload, SportsBeneficiaryPayload
from src.schemas.MedicalRequestPayload import MedicalRequestPayload, PatientPayload
from src.schemas.EducationRequestPayload import EducationRequestPayload, StudentPayload
from src.schemas.ClothesRequestPayload import ClothesRequestPayload, BeneficiaryPayload
from src.schemas.FoodRequestPayload import CookedFoodResponse, FoodDailyMealRequestPayload, GroceryRequestPayload, GroceryItemPayload
from src.models.types import RequestCategory, SwitchUser, User
from src.models.types import RequestStatusMaster
from src.models.types import UrgencyLevel
from src.db.session import get_db
from src.models.types import UserType
from src.models.types import TypeDonor
from src.models.types import Gender
import logging
from pydantic import BaseModel



from src.core.dependencies import get_current_user_id

# Configure logging
logger = logging.getLogger("api.types")
logging.basicConfig(level=logging.INFO)

# Global response helpers
def success_response(data: Any = None, message: str = "Success"):
    return {"success": True, "message": message, "data": data if data is not None else {}}

def error_response(message: str = "Error", error: Any = None):
    return {"success": False, "message": message, "error": error}

# Pydantic models for POST/PUT
class SwitchUserRequest(BaseModel):
    user_id: int
    switched_to_type: int

router = APIRouter(
    prefix="/api/v1/types",
    tags=["Types"],
    # dependencies=[Depends(get_current_user_id)]
)

public_router = APIRouter(
    prefix="/api/v1/types",
    tags=["Types"]
)


@router.get("/receiver-categories", response_model=dict)
async def get_request_categories(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(RequestCategory))
        request_categories = result.scalars().all() or []
        data = [
            {"id": rc.id, "category_id": rc.category_id, "category_type": rc.category_type, "backgroundColor": rc.backgroundColor, "icon": rc.icon} for rc in request_categories
        ]
        return success_response(data=data, message="Fetched receiver categories")
    except Exception as e:
        logger.error(f"Error in get_request_categories: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch receiver categories", str(e)))


@router.get("/current-userdata/{user_id}", response_model=dict)
async def get_users(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        from src.models.types import Attachment, TypeDonor, UserType
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=error_response("User not found"))
        # Build attachment info if present
        attachment = None
        if hasattr(user, 'attachment_id') and user.attachment_id:
            attach_result = await db.execute(select(Attachment).where(Attachment.id == user.attachment_id))
            attachment_obj = attach_result.scalar_one_or_none()
            if attachment_obj:
                attachment = AttachmentResponse(
                    id=attachment_obj.id,
                    document_type_id=attachment_obj.document_type_id,
                    user_id=attachment_obj.user_id,
                    request_id=attachment_obj.request_id,
                    file_path=attachment_obj.file_path,
                    category_id=attachment_obj.category_id,
                    created_at=str(attachment_obj.created_at) if attachment_obj.created_at else None
                )

        # Bring type_donor name
        type_donor_name = None
        if hasattr(user, 'type_donor_id') and user.type_donor_id:
            td_result = await db.execute(select(TypeDonor).where(TypeDonor.id == user.type_donor_id))
            td_obj = td_result.scalar_one_or_none()
            if td_obj:
                type_donor_name = td_obj.name

        # Bring user_type name (donor_type_subtype)
        user_type_name = None
        if hasattr(user, 'donor_type_subtype') and user.donor_type_subtype:
            ut_result = await db.execute(select(UserType).where(UserType.id == user.donor_type_subtype))
            ut_obj = ut_result.scalar_one_or_none()
            if ut_obj:
                user_type_name = ut_obj.name

        data = UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            organization_name=user.organization_name,
            city=user.city,
            pincode=user.pincode,
            address=user.address,
            state=user.state,
            attachment=attachment,
            user_type=type_donor_name,
            user_subtype=user_type_name
        )
        return success_response(data=data.dict(), message="Fetched user profile")
    except Exception as e:
        logger.error(f"Error in get_users: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch user data", str(e)))



@public_router.get("/user-subtypes", response_model=dict)
async def get_user_types(
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(UserType))
        user_types = result.scalars().all() or []
        data = [{"id": ut.id, "name": ut.name} for ut in user_types]
        return success_response(data=data, message="Fetched user subtypes")
    except Exception as e:
        logger.error(f"Error in get_user_types: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch user subtypes", str(e)))



@public_router.get("/user-types", response_model=dict)
async def get_donor_types(
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(TypeDonor).where(TypeDonor.flag == 1))
        donor_types = result.scalars().all() or []
        data = [
            {"id": dt.id, "name": dt.name, "icon": dt.icon, "icon_color": dt.icon_color, "icon_bg": dt.icon_bg, "description": dt.description} for dt in donor_types
        ]
        return success_response(data=data, message="Fetched donor types")
    except Exception as e:
        logger.error(f"Error in get_donor_types: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch donor types", str(e)))

# Example FastAPI endpoint


@router.get("/genders", response_model=dict)
async def get_genders(
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(Gender))
        genders = result.scalars().all() or []
        data = [{"id": g.id, "gender_name": g.gender_name} for g in genders]
        return success_response(data=data, message="Fetched genders")
    except Exception as e:
        logger.error(f"Error in get_genders: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch genders", str(e)))


# Switch User endpoints (for testing purposes)
@router.post("/switch-users-admin-specific", response_model=dict)
async def create_switch_user(
    payload: SwitchUserRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        new_switch = SwitchUser(
            user_id=payload.user_id,
            switched_to_type=payload.switched_to_type
        )
        db.add(new_switch)
        await db.commit()
        await db.refresh(new_switch)
        data = {
            "id": new_switch.id,
            "user_id": new_switch.user_id,
            "switched_to_type": new_switch.switched_to_type,
            "switched_at": new_switch.switched_at.isoformat()
        }
        return success_response(data=data, message="Switch user created")
    except Exception as e:
        logger.error(f"Error in create_switch_user: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to create switch user", str(e)))


# Endpoint to get all switch user records (for testing purposes)
@router.get("/switch-users-admin-specific/{user_id}", response_model=dict)
async def get_switch_users(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(SwitchUser).where(SwitchUser.user_id == user_id))
        switch_users = result.scalars().all() or []
        data = [
            {
                "id": su.id,
                "user_id": su.user_id,
                "switched_to_type": su.switched_to_type,
                "switched_at": su.switched_at.isoformat()
            }
            for su in switch_users
        ]
        return success_response(data=data, message="Fetched switch users")
    except Exception as e:
        logger.error(f"Error in get_switch_users: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch switch users", str(e)))


@router.get("/statuses", response_model=dict)
async def get_request_status_master(
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(RequestStatusMaster))
        request_statuses = result.scalars().all() or []
        data = [{"id": rs.id, "name": rs.name} for rs in request_statuses]
        return success_response(data=data, message="Fetched request statuses")
    except Exception as e:
        logger.error(f"Error in get_request_status_master: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch request statuses", str(e)))


@router.get("/priorities", response_model=dict)
async def get_urgency_levels(
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(UrgencyLevel))
        urgency_levels = result.scalars().all() or []
        data = [{"id": ul.id, "name": ul.name} for ul in urgency_levels]
        return success_response(data=data, message="Fetched urgency levels")
    except Exception as e:
        logger.error(f"Error in get_urgency_levels: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch urgency levels", str(e)))


@router.get("/receiver-requests/counts/{user_id}", response_model=dict)
async def get_my_request_counts(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        query = text(""" 
        SELECT 
            status_id,
            status_name,
            SUM(total) AS total_count
        FROM (
            SELECT rsm.id AS status_id, rsm.name AS status_name, COUNT(sr.id) AS total
            FROM request_status_master rsm
            LEFT JOIN sports_requests sr 
                ON sr.status_id = rsm.id AND sr.user_id = :user_id
            GROUP BY rsm.id, rsm.name
            UNION ALL
            SELECT rsm.id, rsm.name, COUNT(er.id)
            FROM request_status_master rsm
            LEFT JOIN education_requests er 
                ON er.status_id = rsm.id AND er.user_id = :user_id
            GROUP BY rsm.id, rsm.name
            UNION ALL
            SELECT rsm.id, rsm.name, COUNT(mr.id)
            FROM request_status_master rsm
            LEFT JOIN medical_requests mr 
                ON mr.status_id = rsm.id AND mr.user_id = :user_id
            GROUP BY rsm.id, rsm.name
            UNION ALL
            SELECT rsm.id, rsm.name, COUNT(sr.id)
            FROM request_status_master rsm
            LEFT JOIN shelter_requests sr 
                ON sr.status_id = rsm.id AND sr.user_id = :user_id
            GROUP BY rsm.id, rsm.name
            UNION ALL
            SELECT rsm.id, rsm.name, COUNT(cr.id)
            FROM request_status_master rsm
            LEFT JOIN clothes_requests cr 
                ON cr.status_id = rsm.id AND cr.user_id = :user_id
            GROUP BY rsm.id, rsm.name
            UNION ALL
            SELECT rsm.id, rsm.name, COUNT(frcf.id)
            FROM request_status_master rsm
            LEFT JOIN food_requests_cooked_food frcf 
                ON frcf.status_id = rsm.id AND frcf.user_id = :user_id
            GROUP BY rsm.id, rsm.name
            UNION ALL
            SELECT rsm.id, rsm.name, COUNT(fdmr.id)
            FROM request_status_master rsm
            LEFT JOIN food_daily_meal_requests fdmr 
                ON fdmr.status_id = rsm.id AND fdmr.user_id = :user_id
            GROUP BY rsm.id, rsm.name
            UNION ALL
            SELECT rsm.id, rsm.name, COUNT(ger.id)
            FROM request_status_master rsm
            LEFT JOIN grocery_essentials_requests ger 
                ON ger.status_id = rsm.id AND ger.user_id = :user_id
            GROUP BY rsm.id, rsm.name
        ) AS combined
        GROUP BY status_id, status_name
        ORDER BY status_id;
        """)

        result = await db.execute(query, {"user_id": user_id})
        rows = result.fetchall() or []

        counts_map = {
            "Pending": 0,
            "Approved": 0,
            "In Progress": 0,
            "Completed": 0,
            "Rejected": 0
        }

        for row in rows:
            counts_map[row.status_name] = row.total_count

        data = {
            "user_id": user_id,
            "counts": {
                "total": sum(counts_map.values()),
                "pending": counts_map["Pending"],
                "approved": counts_map["Approved"],
                "in_progress": counts_map["In Progress"],
                "completed": counts_map["Completed"],
                "rejected": counts_map["Rejected"],
            }
        }
        return success_response(data=data, message="Fetched request counts")
    except Exception as e:
        logger.error(f"Error in get_my_request_counts: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to fetch request counts", str(e)))


@router.get("/receiver-requests/user-filled", response_model=dict)
async def get_all_user_data(
    user_id: Optional[int] = Query(None, gt=0),
    status_id: Optional[int] = Query(None, gt=0),
    category_id: Optional[int] = Query(None, gt=0),
    db: AsyncSession = Depends(get_db),
):
    def build_where_clause_multi(
        user_id, status_id, category_id,
        user_col, status_col,
        category_col=None,
        sub_category_col=None
    ):
        where = []
        params = {}

        if user_id is not None:
            where.append(f"{user_col} = :user_id")
            params["user_id"] = user_id

        if status_id is not None:
            where.append(f"{status_col} = :status_id")
            params["status_id"] = status_id

        if category_id is not None:
            # 👉 FOOD CATEGORY
            if sub_category_col:
                if category_id == 1:
                    where.append(f"{sub_category_col} IN (1,2,3)")
                else:
                    # ❗ Block food if category != 1
                    where.append("1=0")
            # 👉 OTHER CATEGORIES
            elif category_col:
                where.append(f"{category_col} = :category_id")
                params["category_id"] = category_id

        return ("WHERE " + " AND ".join(where)) if where else "", params

    # SHELTER
    shelter_where, shelter_params = build_where_clause_multi(
        user_id, status_id, category_id,
        "sr.user_id", "sr.status_id",
        category_col="sr.category_id")
    shelter_q = await db.execute(text(f"""
    SELECT 
        sr.id,
        sr.user_id,
        rc.category_type AS category,
        sr.category_id,
        rsm.name AS status,
        ul.name AS urgency,
        sr.request_title,
        sr.request_description,
        sb.person_name,
        sb.total_members,
        sb.current_address,
        sb.duration_of_problem,
        sb.number_of_days,
        ssn.name AS special_need,
        sst.name AS staying_type,
        srt.name AS requirement_type,
        sdo.name AS duration_option,
        sr.created_at,
        sr.updated_at,
        at1.file_path as damage_document_filepath,
        at2.file_path as verification_document_filepath
    FROM shelter_requests sr
    LEFT JOIN shelter_beneficiaries sb ON sr.id = sb.shelter_request_id
    LEFT JOIN request_categories rc ON sr.category_id = rc.id
    LEFT JOIN request_status_master rsm ON sr.status_id = rsm.id
    LEFT JOIN urgency_levels ul ON sr.urgency_id = ul.id
    LEFT JOIN shelter_special_needs ssn ON sb.special_need_id = ssn.id
    LEFT JOIN shelter_staying_types sst ON sb.staying_type_id = sst.id
    LEFT JOIN shelter_requirement_types srt ON sb.requirement_type_id = srt.id
    LEFT JOIN shelter_duration_options sdo ON sb.duration_option_id = sdo.id
    LEFT JOIN attachments at1 on sb.damage_document_id = at1.id
    LEFT JOIN attachments at2 on sb.verification_document_id = at2.id
    {shelter_where}
    """), shelter_params)
    shelter = shelter_q.fetchall()

    # SPORTS
    sports_where, sports_params = build_where_clause_multi(user_id, status_id, category_id, "sr.user_id", "sr.status_id", category_col="sr.category_id")
    sports_q = await db.execute(text(f"""
        SELECT 
            sr.id,
            sr.user_id,
            rc.category_type AS category,
            rsm.name AS status,
            ul.name AS urgency,
            sr.request_title,
            sr.request_description,
            srb.person_name,
            srb.age_group,
            g.gender_name AS gender,
            pl.name AS playing_level,
            srb.achievement,
            srb.amount_requested,
            srb.event_date,
            srb.institution_name,
            srb.phone,
            at1.file_path AS verification_document_filepath,
            at2.file_path AS achievement_document_filepath,
            GROUP_CONCAT(DISTINCT sc.name) AS sports_names,
            GROUP_CONCAT(DISTINCT sst.name) AS support_type_names,
            sr.created_at,
            sr.updated_at
        FROM sports_requests sr
        LEFT JOIN sports_request_beneficiaries srb ON sr.id = srb.sports_request_id
        LEFT JOIN request_categories rc ON sr.category_id = rc.id
        LEFT JOIN request_status_master rsm ON sr.status_id = rsm.id
        LEFT JOIN urgency_levels ul ON sr.urgency_id = ul.id
        LEFT JOIN gender g ON srb.gender_id = g.id
        LEFT JOIN playing_levels pl ON srb.playing_level_id = pl.id
        LEFT JOIN sports_categories sc ON JSON_CONTAINS(srb.sports_category_ids, CAST(sc.id AS JSON))
        LEFT JOIN sports_support_type sst ON JSON_CONTAINS(srb.support_type_ids, CAST(sst.id AS JSON))
        LEFT JOIN attachments at1 ON srb.verification_document_id = at1.id
        LEFT JOIN attachments at2 ON srb.achievement_document_id = at2.id
        {sports_where}
        GROUP BY sr.id, srb.id;
    """), sports_params)
    sports = sports_q.fetchall()

    # MEDICAL
    medical_where, medical_params = build_where_clause_multi(user_id, status_id, category_id, "mr.user_id", "mr.status_id", category_col="mr.category_id")
    medical_q = await db.execute(text(f"""
       SELECT 
            mr.id,
            mr.user_id,
            rc.category_type AS category,
            rsm.name AS status,
            ul.name AS urgency,
            mr.request_title,
            mr.request_description,
            p.patient_name,
            p.age,
            g.gender_name AS gender,
            p.medical_condition,
            p.hospital_name,
            p.hospital_address,
            p.doctor_name,
            p.financial_information,
            p.funds_needed_by,
            p.amount_paid,
            p.amount_requested,
            p.contact_information,
            p.emergency_contact_name,
            bg.name AS blood_group,
            mc.name AS medical_category,
            GROUP_CONCAT(DISTINCT sst.name) AS support_type_names,
            at1.file_path AS verification_document_filepath,
            at2.file_path AS prescription_document_filepath,
            at3.file_path AS estimation_document_filepath,
            mr.created_at,
            mr.updated_at
        FROM medical_requests mr
        LEFT JOIN patients p ON mr.id = p.medical_request_id
        LEFT JOIN blood_groups bg ON p.blood_group_id = bg.id
        LEFT JOIN medical_categories mc ON p.medical_category_id = mc.id
        LEFT JOIN gender g ON p.gender_id = g.id
        LEFT JOIN request_categories rc ON mr.category_id = rc.id
        LEFT JOIN request_status_master rsm ON mr.status_id = rsm.id
        LEFT JOIN urgency_levels ul ON mr.urgency_id = ul.id
        LEFT JOIN support_types sst ON JSON_CONTAINS(p.support_type_ids, CAST(sst.id AS JSON))
        LEFT JOIN attachments at1 ON p.attachment_id = at1.id
        LEFT JOIN attachments at2 ON p.prescription_id = at2.id
        LEFT JOIN attachments at3 ON p.estimation_id = at3.id
        {medical_where}
        GROUP BY mr.id, p.id;
    """), medical_params)
    medical = medical_q.fetchall()

    # EDUCATION
    education_where, education_params = build_where_clause_multi(user_id, status_id, category_id, "er.user_id", "er.status_id", category_col="er.category_id")
    edu_q = await db.execute(text(f"""
    SELECT 
        er.id,
        er.user_id,
        rc.category_type AS category,
        rsm.name AS status,
        ul.name AS urgency,
        er.request_title,
        er.request_description,
        es.person_name,
        es.age,
        es.grade_level,
        est.name AS education_support_type,
        es.amount_requested,
        es.institution_name,
        es.institution_address,
        es.contact_person_name,
        es.contact_person_phone,
        at1.file_path AS verification_document_filepath,
        at2.file_path AS achievement_document_filepath,
        er.created_at,
        er.updated_at
    FROM education_requests er
    LEFT JOIN education_request_students es ON er.id = es.education_request_id
    LEFT JOIN request_categories rc ON er.category_id = rc.id
    LEFT JOIN request_status_master rsm ON er.status_id = rsm.id
    LEFT JOIN urgency_levels ul ON er.urgency_id = ul.id
    LEFT JOIN education_support_types est ON es.education_support_type_id = est.id
    LEFT JOIN attachments at1 ON es.verification_document_id = at1.id
    LEFT JOIN attachments at2 ON es.education_support_document_id = at2.id
    {education_where};
    """), education_params)
    education = edu_q.fetchall()

    # CLOTHES
    clothes_where, clothes_params = build_where_clause_multi(user_id, status_id, category_id, "cr.user_id", "cr.status_id", category_col="cr.category_id")
    clothes_q = await db.execute(text(f"""
        SELECT 
            cr.id,
            cr.user_id,
            rc.category_type AS category,
            rsm.name AS status,
            ul.name AS urgency,
            cr.request_title,
            cr.request_description,
            cb.person_name,
            cag.name AS age_group,
            g.gender_name AS gender,
            cc.name AS clothing_category,
            ul2.name AS beneficiary_urgency,
            cb.need_by_date,
            cr.created_at,
            cr.updated_at,
            at1.file_path AS verification_document_filepath,
            at2.file_path AS achievement_document_filepath
        FROM clothes_requests cr
        LEFT JOIN clothes_beneficiaries cb ON cr.id = cb.clothes_request_id
        LEFT JOIN request_categories rc ON cr.category_id = rc.id
        LEFT JOIN request_status_master rsm ON cr.status_id = rsm.id
        LEFT JOIN urgency_levels ul ON cr.urgency_id = ul.id
        LEFT JOIN clothes_age_groups cag ON cb.age_group = cag.id
        LEFT JOIN gender g ON cb.gender_preference = g.id
        LEFT JOIN clothing_categories cc ON cb.clothing_category_id = cc.id
        LEFT JOIN urgency_levels ul2 ON cb.urgency_level_id = ul2.id
        LEFT JOIN attachments at1 ON cb.verification_document_id = at1.id
        LEFT JOIN attachments at2 ON cb.beneficiary_photo_id = at2.id
        {clothes_where};
    """), clothes_params)
    clothes = clothes_q.fetchall()

    # FOOD - COOKED FOOD
    cooked_where, cooked_params = build_where_clause_multi(
    user_id, status_id, category_id,
    "cf.user_id", "cf.status_id",
    sub_category_col="cf.food_request_category_id")
    cooked_q = await db.execute(text(f"""
     SELECT 
        cf.id,
        cf.user_id,
        'Food - Cooked' AS category,
        rsm.name AS status,
        ul.name AS urgency,
        cf.request_title,
        cf.request_description,
        ft.name AS food_type,
        mt.name AS meal_type,
        cf.number_of_people,
        cf.plates_required,
        cf.required_date,
        ts.name AS time_slot,
        ful.name AS food_urgency,
        cf.address,
        cf.landmark,
        cf.delivery_required,
        cf.created_at,
        cf.updated_at
    FROM food_requests_cooked_food cf
    LEFT JOIN food_types ft ON cf.food_type_id = ft.id
    LEFT JOIN food_meal_types mt ON cf.meal_type_id = mt.id
    LEFT JOIN food_time_slots ts ON cf.time_slot_id = ts.id
    LEFT JOIN food_urgency_levels ful ON cf.urgency_level_id = ful.id
    LEFT JOIN request_status_master rsm ON cf.status_id = rsm.id
    LEFT JOIN urgency_levels ul ON cf.urgency_id = ul.id
    {cooked_where};
    """), cooked_params)
    cooked = cooked_q.fetchall()

    daily_where, daily_params = build_where_clause_multi(
    user_id, status_id, category_id,
    "dm.user_id", "dm.status_id",
    sub_category_col="dm.food_request_category_id"
    )
    daily_q = await db.execute(text(f"""
    SELECT 
        dm.id,
        dm.user_id,
        'Food - Daily Meal' AS category,
        rsm.name AS status,
        ul.name AS urgency,
        dm.request_title,
        dm.request_description,
        dm.number_of_people,
        ag.name AS age_group,
        msn.name AS medical_special_need,
        mt.name AS meal_type,
        mf.name AS frequency,
        d.name AS duration,
        dm.custom_days,
        dm.custom_date_range,
        ts.name AS time_slot,
        dm.address,
        dm.landmark,
        dm.delivery_required,
        dm.created_at,
        dm.updated_at
    FROM food_daily_meal_requests dm
    LEFT JOIN food_age_groups ag ON dm.age_group_id = ag.id
    LEFT JOIN food_special_needs msn ON dm.special_need_id = msn.id
    LEFT JOIN food_meal_types mt ON dm.meal_type_id = mt.id
    LEFT JOIN food_meal_frequencies mf ON dm.frequency_id = mf.id
    LEFT JOIN food_durations d ON dm.duration_id = d.id
    LEFT JOIN food_time_slots ts ON dm.time_slot_id = ts.id
    LEFT JOIN request_status_master rsm ON dm.status_id = rsm.id
    LEFT JOIN urgency_levels ul ON dm.urgency_id = ul.id
    {daily_where};
        """), daily_params)
    daily = daily_q.fetchall()
    grocery_where, grocery_params = build_where_clause_multi(
        user_id, status_id, category_id,
        "gr.user_id", "gr.status_id",
        sub_category_col="gr.food_request_category_id"
    )
    grocery_q = await db.execute(text(f"""
     SELECT 
        gr.id,
        gr.user_id,
        'Food - Grocery' AS category,
        rsm.name AS status,
        ul.name AS urgency,
        gr.request_title,
        gr.request_description,
        gf.name AS frequency,
        gr.address,
        gr.landmark,
        gr.delivery_required,
        gim.name AS item_name,
        gi.custom_item_name,
        gi.quantity,
        gu.name AS unit,
        gp.name AS priority,
        gr.created_at,
        gr.updated_at
    FROM grocery_essentials_requests gr
    LEFT JOIN grocery_essentials_items gi ON gr.id = gi.grocery_essentials_request_id
    LEFT JOIN grocery_item_master gim ON gi.item_master_id = gim.id
    LEFT JOIN grocery_unit_options gu ON gi.unit_id = gu.id
    LEFT JOIN grocery_priority_levels gp ON gi.priority_id = gp.id
    LEFT JOIN food_meal_frequencies gf ON gr.frequency_id = gf.id
    LEFT JOIN request_status_master rsm ON gr.status_id = rsm.id
    LEFT JOIN urgency_levels ul ON gr.urgency_id = ul.id
    {grocery_where};
    """), grocery_params)
    grocery = grocery_q.fetchall()

    # NESTED shelter_requests using append
    shelter_map = {}
    shelter_requests = []
    for row in shelter:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in shelter_map:
            # Parent fields
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['beneficiaries'] = []
            shelter_requests.append(parent)
            shelter_map[req_id] = parent
        # Child fields
        child_fields = [
            'person_name', 'total_members', 'current_address', 'duration_of_problem', 'number_of_days',
            'special_need', 'staying_type', 'requirement_type', 'duration_option',
            'damage_document_filepath', 'verification_document_filepath'
        ]

        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            shelter_map[req_id]['beneficiaries'].append(child)

    # # NESTED sports_requests using append
    sports_map = {}
    sports_requests = []
    for row in sports:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in sports_map:
            # Parent fields
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['participants'] = []
            sports_requests.append(parent)
            sports_map[req_id] = parent
        # Child fields
        child_fields = [
            'person_name', 'age_group', 'gender', 'playing_level', 'achievement', 'amount_requested', 'event_date', 'institution_name', 'phone', 'verification_document_filepath', 'achievement_document_filepath', 'sports_names', 'support_type_names'
        ]

        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            sports_map[req_id]['participants'].append(child)

    # NESTED medical_requests using append
    medical_map = {}
    medical_requests = []
    for row in medical:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in medical_map:
            # Parent fields
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['patients'] = []
            medical_requests.append(parent)
            medical_map[req_id] = parent
        # Child fields
        child_fields = [
            'patient_name', 'age', 'gender', 'medical_condition','hospital_name','hospital_address','doctor_name','financial_information','funds_needed_by','amount_paid','amount_requested','contact_information','emergency_contact_name','blood_group','medical_category','support_type_names','verification_document_filepath','prescription_document_filepath','estimation_document_filepath',
        ]

        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            medical_map[req_id]['patients'].append(child)

    # # NESTED education_requests using append
    education_map = {}
    education_requests = []
    for row in education:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in education_map:
            # Parent fields
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['students'] = []
            education_requests.append(parent)
            education_map[req_id] = parent
        # Child fields
        child_fields = [
            'person_name', 'age', 'grade', 'education_support_type', 'amount_requested', 'institution_name', 'institution_address', 'contact_person_name', 'contact_person_phone', 'verification_document_filepath', 'achievement_document_filepath'
        ]

        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            education_map[req_id]['students'].append(child)

    # # NESTED clothes_requests using append
    clothes_map = {}
    clothes_requests = []
    for row in clothes:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in clothes_map:
            # Parent fields
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['items'] = []
            clothes_requests.append(parent)
            clothes_map[req_id] = parent
        # Child fields
        child_fields = [
            'person_name', 'age_group', 'gender', 'clothing_category', 'beneficiary_urgency', 'need_by_date', 'verification_document_filepath', 'achievement_document_filepath'
        ]

        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            clothes_map[req_id]['items'].append(child)

    # # NESTED grocery_essentials_requests using append
    grocery_map = {}
    grocery_requests = []
    for row in grocery:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in grocery_map:
            # Parent fields
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'address', 'landmark', 'delivery_required', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['items'] = []
            grocery_requests.append(parent)
            grocery_map[req_id] = parent
        # Child fields
        child_fields = [
            'frequency', 'item_name', 'custom_item_name', 'quantity', 'unit', 'priority'
        ]
        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            grocery_map[req_id]['items'].append(child)

        # end for

    return success_response(data={
        "shelter_requests": shelter_requests,
        "sports_requests": sports_requests,
        "medical_requests": medical_requests,
        "education_requests": education_requests,
        "clothes_requests": clothes_requests,
        "food_requests_cooked_food": [dict(row._mapping) for row in cooked],
        "food_daily_meal_requests": [dict(row._mapping) for row in daily],
        "grocery_essentials_requests": grocery_requests,
    }, message="Fetched all user data")


@router.put("/people-in-need/update-and-get", response_model=dict)
async def update_and_get_people_in_need(db: AsyncSession = Depends(get_db)):
    try:
        update_query = text("""
        UPDATE people_in_need pin
        JOIN (
            SELECT 
                rc.id AS category_id,
                COALESCE(SUM(data.amount_requested), 0) AS total_amount_requested
            FROM request_categories rc
            LEFT JOIN (
                SELECT 6 AS category_id, sb.amount_requested
                FROM sports_request_beneficiaries sb
                JOIN sports_requests sr ON sb.sports_request_id = sr.id
                WHERE sr.status_id = 2
                UNION ALL
                SELECT 5, sh.amount_requested
                FROM shelter_beneficiaries sh
                JOIN shelter_requests sr ON sh.shelter_request_id = sr.id
                WHERE sr.status_id = 2
                UNION ALL
                SELECT 3, es.amount_requested
                FROM education_request_students es
                JOIN education_requests er ON es.education_request_id = er.id
                WHERE er.status_id = 2
                UNION ALL
                SELECT 4, p.amount_requested
                FROM patients p
                JOIN medical_requests mr ON p.medical_request_id = mr.id
                WHERE mr.status_id = 2
                UNION ALL
                SELECT 2, cb.amount_requested
                FROM clothes_beneficiaries cb
                JOIN clothes_requests cr ON cb.clothes_request_id = cr.id
                WHERE cr.status_id = 2
                UNION ALL
                SELECT 1, ge.amount_requested
                FROM grocery_essentials_requests ge
                WHERE ge.status_id = 2
                UNION ALL
                SELECT 1, fd.amount_requested
                FROM food_daily_meal_requests fd
                WHERE fd.status_id = 2)data
            ON rc.id = data.category_id
            GROUP BY rc.id
        ) agg
        ON pin.category_id = agg.category_id
        SET pin.amount_requested = agg.total_amount_requested
        WHERE pin.id > 0;
        """)

        await db.execute(update_query)

        select_query = text("""
        SELECT 
            pin.id,
            pin.category_id,
            rc.category_type,
            pin.amount_requested,
            pin.description,
            pin.color,
            pin.created_at,
            pin.updated_at
        FROM people_in_need pin
        JOIN request_categories rc 
            ON pin.category_id = rc.id
        ORDER BY pin.category_id;
        """)

        result = await db.execute(select_query)
        rows = result.fetchall() or []

        await db.commit()

        data = [dict(row._mapping) for row in rows]
        return success_response(data=data, message="Updated and fetched people in need")
    except Exception as e:
        logger.error(f"Error in update_and_get_people_in_need: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=error_response("Failed to update/fetch people in need", str(e)))