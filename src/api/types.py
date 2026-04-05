from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from src.models.types import SwitchUser, User
from src.models.types import RequestStatusMaster
from src.models.types import UrgencyLevel
from src.db.session import get_db
from src.models.types import UserType
from src.models.types import TypeDonor
from src.models.types import Gender
from src.core.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1/types", tags=["Types"])

@router.get("/users", response_model=list[dict])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{"id": u.id, "name": u.name} for u in users]

@router.get("/user-types", response_model=list[dict])
async def get_user_types(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(select(UserType))
    user_types = result.scalars().all()
    return [
        {"id": ut.id, "name": ut.name} for ut in user_types
    ]

@router.get("/donor-types", response_model=list[dict])
async def get_donor_types(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(select(TypeDonor))
    donor_types = result.scalars().all()
    return [
        {"id": dt.id, "name": dt.name} for dt in donor_types
    ]

# Example FastAPI endpoint

@router.get("/genders", response_model=list[dict])
async def get_genders(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(select(Gender))
    genders = result.scalars().all()
    return [{"id": g.id, "gender_name": g.gender_name} for g in genders]

# Switch User endpoints (for testing purposes)
@router.post("/switch-users", response_model=dict)
async def create_switch_user(
    user_id: int,
    switched_to_type: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    new_switch = SwitchUser(
        user_id=user_id,
        switched_to_type=switched_to_type
    )
    db.add(new_switch)
    await db.commit()
    await db.refresh(new_switch)
    return {
        "id": new_switch.id,
        "user_id": new_switch.user_id,
        "switched_to_type": new_switch.switched_to_type,
        "switched_at": new_switch.switched_at.isoformat()
    }

# Endpoint to get all switch user records (for testing purposes)
@router.get("/switch-users/{user_id}", response_model=list[dict])
async def get_switch_users(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(select(SwitchUser).where(SwitchUser.user_id == user_id))
    switch_users = result.scalars().all()
    return [
        {
            "id": su.id,
            "user_id": su.user_id,
            "switched_to_type": su.switched_to_type,
            "switched_at": su.switched_at.isoformat()
        }
        for su in switch_users
    ]

@router.get("/request-status-master", response_model=list[dict])
async def get_request_status_master(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(select(RequestStatusMaster))
    request_statuses = result.scalars().all()
    return [{"id": rs.id, "name": rs.name} for rs in request_statuses]

@router.get("/urgency-levels", response_model=list[dict])
async def get_urgency_levels(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(select(UrgencyLevel))
    urgency_levels = result.scalars().all()
    return [{"id": ul.id, "name": ul.name} for ul in urgency_levels]

@router.get("/user-full-data/{user_id}")
async def get_all_user_data(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own data",
        )

    # SHELTER
    shelter_q = await db.execute(text("""
    SELECT 
        sr.id,
        sr.user_id,

        rc.category_type AS category,
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
        sr.updated_at

    FROM shelter_requests sr

    LEFT JOIN shelter_beneficiaries sb 
        ON sr.id = sb.shelter_request_id

    LEFT JOIN request_categories rc 
        ON sr.category_id = rc.id

    LEFT JOIN request_status_master rsm 
        ON sr.status_id = rsm.id

    LEFT JOIN urgency_levels ul 
        ON sr.urgency_id = ul.id

    LEFT JOIN shelter_special_needs ssn 
        ON sb.special_need_id = ssn.id

    LEFT JOIN shelter_staying_types sst 
        ON sb.staying_type_id = sst.id

    LEFT JOIN shelter_requirement_types srt 
        ON sb.requirement_type_id = srt.id

    LEFT JOIN shelter_duration_options sdo 
    ON sb.duration_option_id = sdo.id

    WHERE sr.user_id = :user_id
    """), {"user_id": user_id})

    shelter = shelter_q.fetchall()

    # SPORTS
    sports_q = await db.execute(text("""
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
            sc.name AS sports_category,

            sr.created_at,
            sr.updated_at

        FROM sports_requests sr

        LEFT JOIN sports_request_beneficiaries srb 
            ON sr.id = srb.sports_request_id

        LEFT JOIN request_categories rc 
            ON sr.category_id = rc.id

        LEFT JOIN request_status_master rsm 
            ON sr.id = rsm.id

        LEFT JOIN urgency_levels ul 
            ON sr.id = ul.id

        LEFT JOIN gender g 
            ON srb.gender_id = g.id

        LEFT JOIN playing_levels pl 
            ON srb.id = pl.id

        LEFT JOIN sports_categories sc 
            ON srb.id = sc.id

        WHERE sr.user_id = :user_id
            """), {"user_id": user_id})

    sports = sports_q.fetchall()

    # MEDICAL
    medical_q = await db.execute(text("""
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
            bg.name AS blood_group,
            mc.name AS medical_category,

            st.name AS support_type,

            mr.created_at,
            mr.updated_at

        FROM medical_requests mr

        LEFT JOIN patients p 
            ON mr.id = p.medical_request_id

        LEFT JOIN patient_support_types pst 
            ON p.id = pst.patient_id

        LEFT JOIN support_types st 
            ON pst.support_type_id = st.id

        LEFT JOIN blood_groups bg 
            ON p.blood_group_id = bg.id

        LEFT JOIN medical_categories mc 
            ON p.medical_category_id = mc.id

        LEFT JOIN gender g 
            ON p.gender_id = g.id

        LEFT JOIN request_categories rc 
            ON mr.category_id = rc.id

        LEFT JOIN request_status_master rsm 
            ON mr.status_id = rsm.id

        LEFT JOIN urgency_levels ul 
            ON mr.urgency_id = ul.id

        WHERE mr.user_id = :user_id;
    """), {"user_id": user_id})

    medical = medical_q.fetchall()

    # EDUCATION
    edu_q = await db.execute(text("""
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

        es.verification_document_id,
        es.education_support_document_id,

        er.created_at,
        er.updated_at

    FROM education_requests er

    LEFT JOIN education_request_students es 
        ON er.id = es.education_request_id

    LEFT JOIN request_categories rc 
        ON er.category_id = rc.id

    LEFT JOIN request_status_master rsm 
        ON er.status_id = rsm.id

    LEFT JOIN urgency_levels ul 
        ON er.urgency_id = ul.id

    LEFT JOIN education_support_types est 
        ON es.education_support_type_id = est.id

    WHERE er.user_id = :user_id;
    """), {"user_id": user_id})

    education = edu_q.fetchall()

    # CLOTHES
    clothes_q = await db.execute(text("""
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

            cb.verification_document_id,
            cb.beneficiary_photo_id,

            cr.created_at,
            cr.updated_at

        FROM clothes_requests cr

        LEFT JOIN clothes_beneficiaries cb 
            ON cr.id = cb.clothes_request_id

        LEFT JOIN request_categories rc 
            ON cr.category_id = rc.id

        LEFT JOIN request_status_master rsm 
            ON cr.status_id = rsm.id

        LEFT JOIN urgency_levels ul 
            ON cr.urgency_id = ul.id

        LEFT JOIN clothes_age_groups cag 
            ON cb.age_group = cag.id

        LEFT JOIN gender g 
            ON cb.gender_preference = g.id

        LEFT JOIN clothing_categories cc 
            ON cb.clothing_category_id = cc.id

        LEFT JOIN urgency_levels ul2 
            ON cb.urgency_level_id = ul2.id

        WHERE cr.user_id = :user_id;
    """), {"user_id": user_id})

    clothes = clothes_q.fetchall()

    return {
        "user_id": user_id,
        "data": {
            "shelter": [dict(row._mapping) for row in shelter],
            "sports": [dict(row._mapping) for row in sports],
            "medical": [dict(row._mapping) for row in medical],
            "education": [dict(row._mapping) for row in education],
            "clothes": [dict(row._mapping) for row in clothes],
        }
    }

    

   


    