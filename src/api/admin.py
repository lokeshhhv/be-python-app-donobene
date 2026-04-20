from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text


from src.models.shelter import ShelterBeneficiary, ShelterRequest
from src.models.types import Attachment
from src.models.sports import SportsRequest, SportsRequestBeneficiary
from src.models.clothes import ClothesRequest, ClothesRequestBeneficiaries, ClothesRequestBeneficiariesSizes
from src.models.medical import MedicalRequest, Patient
from src.models.education import EducationRequest, EducationRequestStudents
from src.db.session import get_db
from src.core.dependencies import get_current_user_id

from fastapi import Query

router = APIRouter(
    prefix="/api/v1/admin", 
    tags=["Admin"], 
    # dependencies=[Depends(get_current_user_id)]
)

@router.get("/admin-requests-filters")
async def get_filtered_requests(
    status_id: Optional[int] = Query(None, description="Status ID to filter by"),
    category_id: Optional[int] = Query(None, description="Category ID to filter by"),
    food_category_id: Optional[int] = Query(None, description="Food subcategory: 1=cooked, 2=daily, 3=grocery"),
    db: AsyncSession = Depends(get_db)
):
    # Shelter
    shelter_q = text("""
        SELECT 
        sr.id,
		u.name,
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
    
    LEFT JOIN users u
    ON u.id = sr.user_id

    WHERE
        (:status_id IS NULL OR sr.status_id = :status_id)
        AND (:category_id IS NULL OR sr.category_id = :category_id)
    """)

    # SPORTS:
    sports_q = text("""
       SELECT 
        sr.id,

        u.name as user_name,
        rc.category_type AS category,
        rsm.name AS status,
        ul.name AS urgency,

        sr.request_title,
        sr.request_description,
        sr.created_at,
        sr.updated_at,
        
        srb.person_name,
        srb.age_group,
        g.gender_name AS gender,
        pl.name AS playing_level,
        srb.achievement,
        srb.amount_requested,
        srb.event_date,
        srb.institution_name,
        srb.phone,

        att1.file_path as verification_document,
        att2.file_path as achievement_document,

        -- ✅ safer aggregation
        GROUP_CONCAT(DISTINCT sc.name ORDER BY sc.name) AS sports_category_name,
        GROUP_CONCAT(DISTINCT sst.name ORDER BY sst.name) AS sports_support_name

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

    LEFT JOIN users u
        ON u.id = sr.user_id

    LEFT JOIN attachments att1
        ON srb.verification_document_id = att1.id

    LEFT JOIN attachments att2
        ON srb.achievement_document_id = att2.id

    LEFT JOIN sports_categories sc 
        ON JSON_CONTAINS(srb.sports_category_ids, CAST(sc.id AS JSON))

    LEFT JOIN sports_support_type sst 
        ON JSON_CONTAINS(srb.support_type_ids, CAST(sst.id AS JSON))

    WHERE (:status_id IS NULL OR sr.status_id = :status_id)
    AND (:category_id IS NULL OR sr.category_id = :category_id)

    GROUP BY 
        sr.id,
        u.name,
        rc.category_type,
        rsm.name,
        ul.name,
        sr.request_title,
        sr.request_description,
        sr.created_at,
        sr.updated_at,
        srb.person_name,
        srb.age_group,
        g.gender_name,
        pl.name,
        srb.achievement,
        srb.amount_requested,
        srb.event_date,
        srb.institution_name,
        srb.phone,
        att1.file_path,
        att2.file_path;
                    
    """)

    # Medical:
    medical_q = text(""" 
        SELECT 
        mr.id,
        u.name as user_name,
        rc.category_type as category_name,
        rsm.name as status_name,
        ul.name as urgency_name,

        mr.request_title,
        mr.request_description,
        mr.created_at,
        mr.updated_at,
        mr.verified,
        mr.reject_reason,
        
        p.medical_request_id,
        p.patient_name,
        p.age,
        g.gender_name,
        p.medical_condition,
        bg.name as blood_group_name,
        mc.name as medical_category_name,
        p.hospital_name,
        p.hospital_address,
        p.doctor_name,
        p.financial_information,
        p.amount_paid,
        p.amount_requested,
        p.funds_needed_by,
        p.contact_information,
        p.emergency_contact_name,

        GROUP_CONCAT(DISTINCT st.name ORDER BY st.name) AS support_type_names,

        at1.file_path AS verification_document_filepath,
        at2.file_path AS prescription_document_filepath,
        at3.file_path AS estimation_document_filepath

    FROM medical_requests mr

    LEFT JOIN patients p
        ON mr.id = p.medical_request_id

    LEFT JOIN users u
        ON u.id = mr.user_id

    LEFT JOIN request_categories rc 
        ON rc.id = mr.category_id

    LEFT JOIN request_status_master rsm 
        ON rsm.id = mr.status_id

    LEFT JOIN urgency_levels ul 
        ON ul.id = mr.urgency_id

    LEFT JOIN gender g
        ON g.id = p.gender_id

    LEFT JOIN blood_groups bg
        ON p.blood_group_id = bg.id

    LEFT JOIN medical_categories mc
        ON p.medical_category_id = mc.id

    -- ✅ FIXED JSON JOIN
    LEFT JOIN support_types st
        ON JSON_CONTAINS(p.support_type_ids, CAST(st.id AS JSON))

    LEFT JOIN attachments at1 
        ON p.attachment_id = at1.id

    LEFT JOIN attachments at2 
        ON p.prescription_id = at2.id

    LEFT JOIN attachments at3 
        ON p.estimation_id = at3.id
                        
    WHERE (:status_id IS NULL OR mr.status_id = :status_id)
        AND (:category_id IS NULL OR mr.category_id = :category_id)

    GROUP BY 
    mr.id,
    u.name,
    rc.category_type,
    rsm.name,
    ul.name,
    mr.request_title,
    mr.request_description,
    mr.created_at,
    mr.updated_at,
    mr.verified,
    mr.reject_reason,
    p.id,
    p.medical_request_id,
    p.patient_name,
    p.age,
    g.gender_name,
    p.medical_condition,
    bg.name,
    mc.name,
    p.hospital_name,
    p.hospital_address,
    p.doctor_name,
    p.financial_information,
    p.amount_paid,
    p.amount_requested,
    p.funds_needed_by,
    p.contact_information,
    p.emergency_contact_name,
    at1.file_path,
    at2.file_path,
    at3.file_path;
    """)

    # Education:
    education_q = text(""" 
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
	LEFT JOIN attachments at1 ON es.verification_document_id = at1.id
    LEFT JOIN attachments at2 ON es.education_support_document_id = at2.id
    WHERE (:status_id IS NULL OR er.status_id = :status_id)
        AND (:category_id IS NULL OR er.category_id = :category_id)
    """)

    # Clothes:
    clothes_q = text(""" 
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

            at1.file_path AS verification_document_filepath,
            at2.file_path AS achievement_document_filepath,
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
		LEFT JOIN attachments at1 ON cb.verification_document_id = at1.id
        LEFT JOIN attachments at2 ON cb.beneficiary_photo_id = at2.id

        WHERE (:status_id IS NULL OR cr.status_id = :status_id)
        AND (:category_id IS NULL OR cr.category_id = :category_id)
    """)

    # Food:
    cooked_food_q = text(""" 
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

    WHERE (:status_id IS NULL OR cf.status_id = :status_id)
        AND (:category_id IS NULL OR cf.food_request_category_id = :category_id)
    """)

    daily_meal_q = text(""" 
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
    
    WHERE (:status_id IS NULL OR dm.status_id = :status_id)
        AND (:category_id IS NULL OR dm.food_request_category_id = :category_id)
    """)

    grocery_q = text(""" 
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
        
    WHERE (:status_id IS NULL OR gr.status_id = :status_id)
        AND (:category_id IS NULL OR gr.food_request_category_id = :category_id)
    """)

    food_categories = {1}
    clothes_categories = {2}
    education_categories = {3}
    medical_categories = {4}
    shelter_categories = {5}
    sports_categories = {6}

    category_query_map = {
        1: [cooked_food_q, daily_meal_q, grocery_q],
        2: [clothes_q],
        3: [education_q],
        4: [medical_q],
        5: [shelter_q],
        6: [sports_q],
    }

    queries_to_run = []
    if food_category_id:
        queries_to_run.extend(category_query_map[1])
    elif category_id:
        queries_to_run.extend(category_query_map.get(category_id, []))
    else: 
        for cat_id in category_query_map:
            queries_to_run.extend(category_query_map[cat_id])

    # Collect all results by category
    shelter_results, sports_results, medical_results, education_results, clothes_results, grocery_results = [], [], [], [], [], []
    cooked_results, daily_results = [], []
    for idx, query in enumerate(queries_to_run):
        result = await db.execute(query, {"status_id": status_id, "category_id": category_id})
        rows = result.fetchall()
        # Assign to correct category
        if query == shelter_q:
            shelter_results.extend(rows)
        elif query == sports_q:
            sports_results.extend(rows)
        elif query == medical_q:
            medical_results.extend(rows)
        elif query == education_q:
            education_results.extend(rows)
        elif query == clothes_q:
            clothes_results.extend(rows)
        elif query == grocery_q:
            grocery_results.extend(rows)
        elif query == cooked_food_q:
            cooked_results.extend(rows)
        elif query == daily_meal_q:
            daily_results.extend(rows)

    # NESTED shelter_requests
    shelter_map = {}
    shelter_requests = []
    for row in shelter_results:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in shelter_map:
            parent_fields = [
                'id', 'name', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['beneficiaries'] = []
            shelter_requests.append(parent)
            shelter_map[req_id] = parent
        child_fields = [
            'person_name', 'total_members', 'current_address', 'duration_of_problem', 'number_of_days',
            'special_need', 'staying_type', 'requirement_type', 'duration_option'
        ]
        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            shelter_map[req_id]['beneficiaries'].append(child)

    # NESTED sports_requests
    sports_map = {}
    sports_requests = []
    for row in sports_results:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in sports_map:
            parent_fields = [
                'id', 'user_name', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['participants'] = []
            sports_requests.append(parent)
            sports_map[req_id] = parent
        child_fields = [
            'person_name', 'age_group', 'gender', 'playing_level', 'achievement', 'amount_requested', 'event_date', 'institution_name', 'phone', 'verification_document', 'achievement_document', 'sports_category_name', 'sports_support_name'
        ]
        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            sports_map[req_id]['participants'].append(child)

    # NESTED medical_requests
    medical_map = {}
    medical_requests = []
    for row in medical_results:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in medical_map:
            parent_fields = [
                'id', 'user_name', 'category_name', 'status_name', 'urgency_name',
                'request_title', 'request_description', 'created_at', 'updated_at', 'verified', 'reject_reason'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['patients'] = []
            medical_requests.append(parent)
            medical_map[req_id] = parent
        child_fields = [
            'medical_request_id', 'patient_name', 'age', 'gender_name', 'medical_condition', 'blood_group_name', 'medical_category_name', 'hospital_name', 'hospital_address', 'doctor_name', 'financial_information', 'amount_paid', 'amount_requested', 'funds_needed_by', 'contact_information', 'emergency_contact_name', 'support_type_names', 'verification_document_filepath', 'prescription_document_filepath', 'estimation_document_filepath'
        ]
        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            medical_map[req_id]['patients'].append(child)

    # NESTED education_requests
    education_map = {}
    education_requests = []
    for row in education_results:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in education_map:
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['students'] = []
            education_requests.append(parent)
            education_map[req_id] = parent
        child_fields = [
            'person_name', 'age', 'grade_level', 'education_support_type', 'amount_requested', 'institution_name', 'institution_address', 'contact_person_name', 'contact_person_phone', 'verification_document_filepath', 'achievement_document_filepath'
        ]
        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            education_map[req_id]['students'].append(child)

    # NESTED clothes_requests
    clothes_map = {}
    clothes_requests = []
    for row in clothes_results:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in clothes_map:
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['items'] = []
            clothes_requests.append(parent)
            clothes_map[req_id] = parent
        child_fields = [
            'person_name', 'age_group', 'gender', 'clothing_category', 'beneficiary_urgency', 'need_by_date', 'verification_document_filepath', 'achievement_document_filepath'
        ]
        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            clothes_map[req_id]['items'].append(child)

    # NESTED grocery_essentials_requests
    grocery_map = {}
    grocery_requests = []
    for row in grocery_results:
        row_dict = dict(row._mapping)
        req_id = row_dict.get('id')
        if req_id not in grocery_map:
            parent_fields = [
                'id', 'user_id', 'category', 'status', 'urgency',
                'request_title', 'request_description', 'address', 'landmark', 'delivery_required', 'created_at', 'updated_at'
            ]
            parent = {k: row_dict[k] for k in parent_fields if k in row_dict}
            parent['items'] = []
            grocery_requests.append(parent)
            grocery_map[req_id] = parent
        child_fields = [
            'frequency', 'item_name', 'custom_item_name', 'quantity', 'unit', 'priority'
        ]
        child = {k: row_dict[k] for k in child_fields if k in row_dict}
        if any(child.values()):
            grocery_map[req_id]['items'].append(child)

    # Flat food cooked/daily (no nesting needed)
    food_requests_cooked_food = [dict(row._mapping) for row in cooked_results]
    food_daily_meal_requests = [dict(row._mapping) for row in daily_results]

    return {
        "shelter_requests": shelter_requests,
        "sports_requests": sports_requests,
        "medical_requests": medical_requests,
        "education_requests": education_requests,
        "clothes_requests": clothes_requests,
        "food_requests_cooked_food": food_requests_cooked_food,
        "food_daily_meal_requests": food_daily_meal_requests,
        "grocery_essentials_requests": grocery_requests,
    }

   


@router.post("/admin-approve-reject")
async def admin_approve_reject(
    request_id: int = Body(..., description="Request ID"),
    request_type: str = Body(..., description="Type: shelter, food_cooked, food_daily, food_grocery, clothes, education, medical, sports"),
    status_id: int = Body(..., description="4 = approve, 5 = reject"),
    verified: bool = Body(..., description="Verified checkbox"),
    reject_reason: Optional[str] = Body(None, description="Reason for rejection"),
    db: AsyncSession = Depends(get_db)
):
    if status_id not in [4, 5]:
        raise HTTPException(status_code=400, detail="Invalid status")

    if status_id == 5 and (not reject_reason or not reject_reason.strip()):
        raise HTTPException(status_code=400, detail="Reject reason required when rejecting")

    table_map = {
        "shelter": "shelter_requests",
        "clothes": "clothes_requests",
        "education": "education_requests",
        "medical": "medical_requests",
        "sports": "sports_requests",
        "food_cooked": "food_requests_cooked_food",
        "food_daily": "food_daily_meal_requests",
        "food_grocery": "grocery_essentials_requests",
    }

    table_name = table_map.get(request_type)
    if not table_name:
        raise HTTPException(status_code=400, detail="Invalid request type")

    # Check record exists
    query = text(f"SELECT id FROM {table_name} WHERE id = :id")
    result = await db.execute(query, {"id": request_id})
    request = result.fetchone()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Update
    # Assumes columns 'status_id', 'verified', and 'reject_reason' exist in all tables. Adjust if needed.
    update_query = text(f"""
        UPDATE {table_name}
        SET status_id = :status_id,
            verified = :verified,
            reject_reason = :reject_reason
        WHERE id = :id
    """)

    await db.execute(update_query, {
        "status_id": status_id,
        "verified": verified,
        "reject_reason": reject_reason if status_id == 5 else None,
        "id": request_id
    })

    await db.commit()

    return {"message": "Status updated successfully"}