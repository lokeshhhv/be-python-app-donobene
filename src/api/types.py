from typing import Optional

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

router = APIRouter(
    prefix="/api/v1/types", 
    tags=["Types"], 
    dependencies=[Depends(get_current_user_id)]
)

@router.get("/current-userdata/{user_id}", response_model=list[dict])
async def get_users(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    from src.models.types import Attachment, TypeDonor, UserType
    result = await db.execute(select(User).where(User.id == user_id))
    users = result.scalars().all()
    user_dicts = []
    for user in users:
        user_data = {k: v for k, v in user.__dict__.items() if not k.startswith('_')}

        # Remove type_donor_id and donor_type_subtype from response
        user_data.pop('type_donor_id', None)
        user_data.pop('donor_type_subtype', None)

        # Bring attachment info if present
        attachment = None
        if hasattr(user, 'attachment_id') and user.attachment_id:
            attach_result = await db.execute(select(Attachment).where(Attachment.id == user.attachment_id))
            attachment_obj = attach_result.scalar_one_or_none()
            if attachment_obj:
                attachment = {k: v for k, v in attachment_obj.__dict__.items() if not k.startswith('_')}
        if attachment:
            user_data['attachment'] = attachment

        # Bring type_donor name
        type_donor_name = None
        if hasattr(user, 'type_donor_id') and user.type_donor_id:
            td_result = await db.execute(select(TypeDonor).where(TypeDonor.id == user.type_donor_id))
            td_obj = td_result.scalar_one_or_none()
            if td_obj:
                type_donor_name = td_obj.name
        user_data['type_donor_name'] = type_donor_name

        # Bring user_type name (donor_type_subtype)
        user_type_name = None
        if hasattr(user, 'donor_type_subtype') and user.donor_type_subtype:
            ut_result = await db.execute(select(UserType).where(UserType.id == user.donor_type_subtype))
            ut_obj = ut_result.scalar_one_or_none()
            if ut_obj:
                user_type_name = ut_obj.name
        user_data['user_type_name'] = user_type_name

        user_dicts.append(user_data)
    return user_dicts

@router.get("/user-types", response_model=list[dict])
async def get_user_types(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserType))
    user_types = result.scalars().all()
    return [
        {"id": ut.id, "name": ut.name} for ut in user_types
    ]

@router.get("/donor-types", response_model=list[dict])
async def get_donor_types(
    db: AsyncSession = Depends(get_db),
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
):
    result = await db.execute(select(RequestStatusMaster))
    request_statuses = result.scalars().all()
    return [{"id": rs.id, "name": rs.name} for rs in request_statuses]

@router.get("/urgency-levels", response_model=list[dict])
async def get_urgency_levels(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UrgencyLevel))
    urgency_levels = result.scalars().all()
    return [{"id": ul.id, "name": ul.name} for ul in urgency_levels]

@router.get("/myrequest-counts/{user_id}", response_model=dict)
async def get_my_request_counts(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
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
    rows = result.fetchall()

    # ✅ Initialize all statuses
    counts_map = {
        "Pending": 0,
        "Approved": 0,
        "In Progress": 0,
        "Completed": 0,
        "Rejected": 0
    }

    # ✅ Fill values from DB
    for row in rows:
        counts_map[row.status_name] = row.total_count

    return {
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

@router.get("/myrequest-user-filled/{user_id}/{status_id}", response_model=dict)
async def get_all_user_data(
    user_id: int,
    status_id: int = None,
    db: AsyncSession = Depends(get_db),
):
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
        sr.updated_at,
        
        at1.file_path as damage_document_filepath,
        at2.file_path as verification_document_filepath

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
    
    LEFT JOIN attachments at1
    on sb.damage_document_id = at1.id
    
    LEFT JOIN attachments at2
    on sb.verification_document_id = at2.id
    WHERE sr.user_id = :user_id and (:status_id IS NULL OR sr.status_id = :status_id)
                                      
    """), {"user_id": user_id, "status_id": status_id})

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

            srb.achievement,
            srb.amount_requested,
            srb.event_date,
            srb.institution_name,
            srb.phone,

            at1.file_path AS verification_document_filepath,
            at2.file_path AS achievement_document_filepath,

            -- 🔥 MULTIPLE VALUES
            GROUP_CONCAT(DISTINCT sc.name) AS sports_names,
            GROUP_CONCAT(DISTINCT sst.name) AS support_type_names,

            sr.created_at,
            sr.updated_at

        FROM sports_requests sr

        LEFT JOIN sports_request_beneficiaries srb 
            ON sr.id = srb.sports_request_id

        LEFT JOIN request_categories rc 
            ON sr.category_id = rc.id

        LEFT JOIN request_status_master rsm 
            ON sr.status_id = rsm.id

        LEFT JOIN urgency_levels ul 
            ON sr.urgency_id = ul.id

        LEFT JOIN gender g 
            ON srb.gender_id = g.id

        LEFT JOIN playing_levels pl 
            ON srb.playing_level_id = pl.id

        -- ✅ JSON FIX
        LEFT JOIN sports_categories sc 
        ON JSON_CONTAINS(srb.sports_category_ids, CAST(sc.id AS JSON))

        LEFT JOIN sports_support_type sst
        ON JSON_CONTAINS(srb.support_type_ids, CAST(sst.id AS JSON))

        LEFT JOIN attachments at1
            ON srb.verification_document_id = at1.id

        LEFT JOIN attachments at2
            ON srb.achievement_document_id = at2.id

        WHERE sr.user_id = :user_id 
        AND (:status_id IS NULL OR sr.status_id = :status_id)

        GROUP BY sr.id, srb.id;
    
    """), {"user_id": user_id, "status_id": status_id})

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

        LEFT JOIN patients p 
            ON mr.id = p.medical_request_id

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

        -- 🔥 JSON FIX
        LEFT JOIN sports_support_type sst 
        ON JSON_CONTAINS(p.support_type_ids, CAST(sst.id AS JSON))

        LEFT JOIN attachments at1 
            ON p.attachment_id = at1.id

        LEFT JOIN attachments at2 
            ON p.prescription_id = at2.id

        LEFT JOIN attachments at3 
            ON p.estimation_id = at3.id

        WHERE mr.user_id = :user_id
        AND (:status_id IS NULL OR mr.status_id = :status_id)

        GROUP BY mr.id, p.id;

    """), {"user_id": user_id , "status_id": status_id})

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

        at1.file_path AS verification_document_filepath,
		at2.file_path AS achievement_document_filepath,

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
	
    LEFT JOIN attachments at1
            ON es.verification_document_id = at1.id

	LEFT JOIN attachments at2
		ON es.education_support_document_id = at2.id
	
    WHERE er.user_id = :user_id and (:status_id IS NULL OR er.status_id = :status_id);
    """), {"user_id": user_id, "status_id": status_id})

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

            cr.created_at,
            cr.updated_at,
			at1.file_path AS verification_document_filepath,
            at2.file_path AS achievement_document_filepath

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
            
		LEFT JOIN attachments at1
            ON cb.verification_document_id = at1.id

        LEFT JOIN attachments at2
            ON cb.beneficiary_photo_id = at2.id

        WHERE cr.user_id = :user_id and (:status_id IS NULL OR cr.status_id = :status_id);
    """), {"user_id": user_id, "status_id": status_id})

    clothes = clothes_q.fetchall()

    # FOOD - COOKED FOOD
    cooked_q = await db.execute(text("""
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

    WHERE cf.user_id = :user_id and (:status_id IS NULL OR cf.status_id = :status_id);
    """), {"user_id": user_id, "status_id": status_id})

    cooked = cooked_q.fetchall()

    daily_q = await db.execute(text("""
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

    WHERE dm.user_id = :user_id and (:status_id IS NULL OR dm.status_id = :status_id);
        """), {"user_id": user_id, "status_id": status_id})

    daily = daily_q.fetchall()

    grocery_q = await db.execute(text("""
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

    LEFT JOIN grocery_essentials_items gi 
        ON gr.id = gi.grocery_essentials_request_id

    LEFT JOIN grocery_item_master gim 
        ON gi.item_master_id = gim.id

    LEFT JOIN grocery_unit_options gu 
        ON gi.unit_id = gu.id

    LEFT JOIN grocery_priority_levels gp 
        ON gi.priority_id = gp.id

    LEFT JOIN food_meal_frequencies gf 
        ON gr.frequency_id = gf.id

    LEFT JOIN request_status_master rsm 
        ON gr.status_id = rsm.id

    LEFT JOIN urgency_levels ul 
        ON gr.urgency_id = ul.id

    WHERE gr.user_id = :user_id and (:status_id IS NULL OR gr.status_id = :status_id);
    """), {"user_id": user_id, "status_id": status_id})

    grocery = grocery_q.fetchall()

    medical_data = {}
    for row in medical:
        row = dict(row._mapping)
        req_id = row["id"]

        if req_id not in medical_data:
            medical_data[req_id] = {
                "id": row["id"],
                "user_id": row["user_id"],
                "category": row["category"],
                "status": row["status"],
                "urgency": row["urgency"],
                "request_title": row["request_title"],
                "request_description": row["request_description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "patients": []
            }

        if row["patient_name"]:
            medical_data[req_id]["patients"].append({
                "patient_name": row["patient_name"],
                "age": row["age"],
                "gender": row["gender"],
                "medical_condition": row["medical_condition"],
                "hospital_name": row["hospital_name"],
                "doctor_name": row["doctor_name"],
                "blood_group": row["blood_group"],
                "medical_category": row["medical_category"],
                "financial_information": row["financial_information"],
                "amount_paid": row["amount_paid"],
                "amount_requested": row["amount_requested"],
                "funds_needed_by": row["funds_needed_by"],
                "contact_information": row["contact_information"],
                "emergency_contact_name": row["emergency_contact_name"],
                "support_type_names": row.get("support_type_names"),
                "verification_document_filepath": row.get("verification_document_filepath"),
                "prescription_document_filepath": row.get("prescription_document_filepath"),
                "estimation_document_filepath": row.get("estimation_document_filepath")
            })

    medical_final = list(medical_data.values())


    shelter_data = {}

    for row in shelter:
        row = dict(row._mapping)
        req_id = row["id"]

        # create parent
        if req_id not in shelter_data:
            shelter_data[req_id] = {
                "id": row["id"],
                "user_id": row["user_id"],
                "category": row["category"],
                "status": row["status"],
                "urgency": row["urgency"],
                "request_title": row["request_title"],
                "request_description": row["request_description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "shelter_beneficiaries": []
            }
        # add beneficiary if exists
        if row["id"]:
            shelter_data[req_id]["shelter_beneficiaries"].append({
                "person_name": row["person_name"],
                "total_members": row["total_members"],
                "current_address": row["current_address"],
                "duration_of_problem": row["duration_of_problem"],
                "number_of_days": row["number_of_days"],
                "special_need": row["special_need"],
                "staying_type": row["staying_type"],
                "requirement_type": row["requirement_type"],
                "duration_option": row["duration_option"],
                "damage_document_filepath": row["damage_document_filepath"],
                "verification_document_filepath": row["verification_document_filepath"]
            })
    shelter_final = list(shelter_data.values())

    sports_data = {}

    for row in sports:
        row = dict(row._mapping)
        req_id = row["id"]

        if req_id not in sports_data:
            sports_data[req_id] = {
                "id": row["id"],
                "user_id": row["user_id"],
                "category": row["category"],
                "status": row["status"],
                "urgency": row["urgency"],
                "request_title": row["request_title"],
                "request_description": row["request_description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "beneficiaries": []
            }

        if row["person_name"]:
            sports_data[req_id]["beneficiaries"].append({
                "person_name": row["person_name"],
                "age_group": row.get("age_group"),
                "gender": row["gender"],
                "playing_level": row["playing_level"],
                "achievement": row["achievement"],
                "amount_requested": row["amount_requested"],
                "event_date": row["event_date"],
                "institution_name": row["institution_name"],
                "phone": row["phone"],
                "verification_document_filepath": row.get("verification_document_filepath"),
                "achievement_document_filepath": row.get("achievement_document_filepath"),
                "sports_names": row.get("sports_names"),
                "support_type_names": row.get("support_type_names")
            })

    sports_final = list(sports_data.values())

    education_data = {}

    for row in education:
        row = dict(row._mapping)
        req_id = row["id"]

        if req_id not in education_data:
            education_data[req_id] = {
                "id": row["id"],
                "user_id": row["user_id"],
                "category": row["category"],
                "status": row["status"],
                "urgency": row["urgency"],
                "request_title": row["request_title"],
                "request_description": row["request_description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "students": []
            }

        if row["person_name"]:
            education_data[req_id]["students"].append({
                "person_name": row["person_name"],
                "age": row["age"],
                "grade_level": row["grade_level"],
                "education_support_type": row["education_support_type"],
                "amount_requested": row["amount_requested"],
                "institution_name": row["institution_name"],
                "institution_address": row["institution_address"],
                "contact_person_name": row["contact_person_name"],
                "contact_person_phone": row["contact_person_phone"],
                "verification_document_filepath": row.get("verification_document_filepath"),
                "achievement_document_filepath": row.get("achievement_document_filepath")
            })

    education_final = list(education_data.values())

    clothes_data = {}

    for row in clothes:
        row = dict(row._mapping)
    req_id = row["id"]

    if req_id not in clothes_data:
        clothes_data[req_id] = {
            "id": row["id"],
            "user_id": row["user_id"],
            "category": row["category"],
            "status": row["status"],
            "urgency": row["urgency"],
            "request_title": row["request_title"],
            "request_description": row["request_description"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "beneficiaries": []
        }

        if row["person_name"]:
            clothes_data[req_id]["beneficiaries"].append({
                "person_name": row["person_name"],
                "age_group": row.get("age_group"),
                "gender": row.get("gender"),
                "clothing_category": row.get("clothing_category"),
                "beneficiary_urgency": row.get("beneficiary_urgency"),
                "need_by_date": row.get("need_by_date"),
                "verification_document_filepath": row.get("verification_document_filepath"),
                "achievement_document_filepath": row.get("achievement_document_filepath")
            })

    clothes_final = list(clothes_data.values())

    grocery_data = {}

    for row in grocery:
        row = dict(row._mapping)
        req_id = row["id"]

        if req_id not in grocery_data:
            grocery_data[req_id] = {
                "id": row["id"],
                "user_id": row["user_id"],
                "category": row["category"],
                "status": row["status"],
                "urgency": row["urgency"],
                "request_title": row["request_title"],
                "request_description": row["request_description"],
                "frequency": row["frequency"],
                "address": row["address"],
                "landmark": row["landmark"],
                "delivery_required": row["delivery_required"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "items": []
            }

        grocery_data[req_id]["items"].append({
            "item_name": row["item_name"],
            "custom_item_name": row["custom_item_name"],
            "quantity": row["quantity"],
            "unit": row["unit"],
            "priority": row["priority"]
        })

    grocery_final = list(grocery_data.values())

    cooked_data = {}

    for row in cooked:
        row = dict(row._mapping)
        req_id = row["id"]

        if req_id not in cooked_data:
            cooked_data[req_id] = {
                "id": row["id"],
                "user_id": row["user_id"],
                "category": row["category"],
                "status": row["status"],
                "urgency": row["urgency"],
                "request_title": row["request_title"],
                "request_description": row["request_description"],
                "number_of_people": row["number_of_people"],
                "plates_required": row["plates_required"],
                "required_date": row["required_date"],
                "address": row["address"],
                "landmark": row["landmark"],
                "delivery_required": row["delivery_required"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "food_details": []
            }

        cooked_data[req_id]["food_details"].append({
            "food_type": row["food_type"],
            "meal_type": row["meal_type"],
            "time_slot": row["time_slot"],
            "food_urgency": row["food_urgency"]
        })

    cooked_final = list(cooked_data.values())

    daily_data = {}

    for row in daily:
        row = dict(row._mapping)
        req_id = row["id"]

        if req_id not in daily_data:
            daily_data[req_id] = {
                "id": row["id"],
                "user_id": row["user_id"],
                "category": row["category"],
                "status": row["status"],
                "urgency": row["urgency"],
                "request_title": row["request_title"],
                "request_description": row["request_description"],
                "number_of_people": row["number_of_people"],
                "address": row["address"],
                "landmark": row["landmark"],
                "delivery_required": row["delivery_required"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "meal_plan": []
            }

        daily_data[req_id]["meal_plan"].append({
            "age_group": row["age_group"],
            "medical_special_need": row["medical_special_need"],
            "meal_type": row["meal_type"],
            "frequency": row["frequency"],
            "duration": row["duration"],
            "custom_days": row["custom_days"],
            "custom_date_range": row["custom_date_range"],
            "time_slot": row["time_slot"]
        })

    daily_final = list(daily_data.values())

    return {
        "user_id": user_id,
        "status_id": status_id,
        "data": {
            "shelter": shelter_final,
            "sports": sports_final,
            "medical": medical_final,
            "education": education_final,
            "clothes": clothes_final,
            "food": {
                "cooked_food": cooked_final,
                "daily_meal": daily_final,
                "grocery": grocery_final
            }
        }
    }

    

   


    