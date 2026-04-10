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


@router.get("/admin-requests-filters/{status_id}/{category_id}")
async def get_filtered_requests(
    status_id: Optional[int] = None,
    category_id: Optional[int] = None,
    food_category_id: Optional[int] = Query(None, description="Food subcategory: 1=cooked, 2=daily, 3=grocery"),
    db: AsyncSession = Depends(get_db)
):
    # Shelter
    shelter_q = text("""
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

    WHERE
        (:status_id IS NULL OR sr.status_id = :status_id)
        AND (:category_id IS NULL OR sr.category_id = :category_id)
    """)

    # SPORTS:
    sports_q = text("""
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
            ON srb.status_id = rsm.id

        LEFT JOIN urgency_levels ul 
            ON srb.urgency_id = ul.id

        LEFT JOIN gender g 
            ON srb.gender_id = g.id

        LEFT JOIN playing_levels pl 
            ON srb.playing_level_id = pl.id

        LEFT JOIN sports_categories sc 
            ON srb.sports_category_id = sc.id
        WHERE (:status_id IS NULL OR srb.status_id = :status_id)
        AND (:category_id IS NULL OR sr.category_id = :category_id)
    """)

    #medical:
    medical_q = text(""" 
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

        WHERE (:status_id IS NULL OR mr.status_id = :status_id)
        AND (:category_id IS NULL OR mr.category_id = :category_id)
    """)

    #Education:
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
	
    WHERE (:status_id IS NULL OR er.status_id = :status_id)
        AND (:category_id IS NULL OR er.category_id = :category_id)
    """)

    #Clothes:
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
            
		WHERE (:status_id IS NULL OR cr.status_id = :status_id)
        AND (:category_id IS NULL OR cr.category_id = :category_id)
    """)

    #Food:
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
   

    if category_id in shelter_categories:
        query = select(ShelterRequest)
        if status_id is not None:
            query = query.where(ShelterRequest.status_id == status_id)
        if category_id is not None:
            query = query.where(ShelterRequest.category_id == category_id)
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

            ben_data = []

            for b in beneficiaries:

                verification_doc = None
                damage_doc = None

                if b.verification_document_id:
                    res = await db.execute(select(Attachment).where(Attachment.id == b.verification_document_id))
                    att = res.scalar_one_or_none()
                    if att:
                        verification_doc = {"id": att.id, "file_path": att.file_path}

                if b.damage_document_id:
                    res = await db.execute(select(Attachment).where(Attachment.id == b.damage_document_id))
                    att = res.scalar_one_or_none()
                    if att:
                        damage_doc = {"id": att.id, "file_path": att.file_path}

                ben_data.append({
                    "id": b.id,
                    "person_name": b.person_name,
                    "total_members": b.total_members,
                    "special_need_id": b.special_need_id,
                    "staying_type_id": b.staying_type_id,
                    "requirement_type_id": b.requirement_type_id,
                    "duration_option_id": b.duration_option_id,
                    "number_of_days": b.number_of_days,
                    "verification_document": verification_doc,
                    "damage_document": damage_doc
                })

            response.append({
                "id": r.id,
                "user_id": r.user_id,
                "category_id": r.category_id,
                "request_title": r.request_title,
                "request_description": r.request_description,
                "status_id": r.status_id,
                "urgency_id": r.urgency_id,
                "verified": r.verified,
                "reject_reason": r.reject_reason,
                "beneficiaries": ben_data
            })
        return response
    elif category_id in sports_categories:
        query = select(SportsRequest)
        if status_id is not None:
            query = query.where(SportsRequest.status_id == status_id)
        if category_id is not None:
            query = query.where(SportsRequest.category_id == category_id)
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

            ben_list = []
            for ben in beneficiaries:
                
                ben_list.append({
                "id": ben.id,
                "person_name": ben.person_name,
                "age_group": ben.age_group,
                "gender_id": ben.gender_id,
                "playing_level_id": ben.playing_level_id,
                "sports_category_ids": ben.sports_category_ids,
                "support_type_ids": ben.support_type_ids,
                "achievement": ben.achievement,
                "amount_requested": ben.amount_requested,
                "event_date": ben.event_date,
                "institution_name": ben.institution_name,
                "phone": ben.phone,
            })
            response.append({
                "id": r.id,
                "user_id": r.user_id,
                "category_id": r.category_id,
                "request_title": r.request_title,
                "request_description": r.request_description,
                "status_id": r.status_id,
                "urgency_id": r.urgency_id,
                "verified": r.verified,
                "reject_reason": r.reject_reason,
                "beneficiaries": ben_list
            })
        return response
    elif category_id in medical_categories:
        query = select(MedicalRequest)
        if status_id is not None:
            query = query.where(MedicalRequest.status_id == status_id)
        if category_id is not None:
            query = query.where(MedicalRequest.category_id == category_id)
        result = await db.execute(query)
        requests = result.scalars().all()

        response = []
        for r in requests:
            patients = (await db.execute(
                select(Patient).where(Patient.medical_request_id == r.id)
            )).scalars().all()
            patient_data = []
            for p in patients:

                patient_data.append({
                "patient_name": p.patient_name,
                "age": p.age,
                "gender_id": p.gender_id,
                "medical_condition": p.medical_condition,
                "blood_group_id": p.blood_group_id,
                "medical_category_id": p.medical_category_id,

                "hospital_name": p.hospital_name,
                "doctor_name": p.doctor_name,
                "amount_requested": float(p.amount_requested) if p.amount_requested else None,

                "support_type_ids": p.support_type_ids,

                "attachment_id": p.attachment_id,
                "prescription_id": p.prescription_id,
                "estimation_id": p.estimation_id
            })

            response.append({
            "id": r.id,
            "user_id": r.user_id,
            "request_title": r.request_title,
            "verified": r.verified,
            "reject_reason": r.reject_reason,
            "patients": patient_data
        })
        return response
    elif category_id in education_categories:
        query = select(EducationRequest)
        if status_id is not None:
            query = query.where(EducationRequest.status_id == status_id)
        if category_id is not None:
            query = query.where(EducationRequest.category_id == category_id)
        result = await db.execute(query)
        requests = result.scalars().all()
        
        response = []
        for r in requests:
            stu_result = await db.execute(
                select(EducationRequestStudents).where(
                    EducationRequestStudents.education_request_id == r.id
                )
            )
            students = stu_result.scalars().all()

            student_data = [
                {
                    "id": s.id,
                    "person_name": s.person_name,
                    "age": s.age,
                    "grade_level": s.grade_level,
                    "education_support_type_id": s.education_support_type_id,
                    "amount_requested": float(s.amount_requested) if s.amount_requested else None,
                    "institution_name": s.institution_name,
                    "college_id": s.college_id,
                    "institution_address": s.institution_address,
                    "contact_person_name": s.contact_person_name,
                    "contact_person_phone": s.contact_person_phone,
                    "verification_document_id": s.verification_document_id,
                    "education_support_document_id": s.education_support_document_id
                }
                for s in students
            ]

            response.append({
                "id": r.id,
                "user_id": r.user_id,
                "category_id": r.category_id,
                "request_title": r.request_title,
                "request_description": r.request_description,
                "status_id": r.status_id,
                "urgency_id": r.urgency_id,
                "verified": r.verified,
                "reject_reason": r.reject_reason,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
                "students": student_data
            }) 
        return response
    elif category_id in clothes_categories:
        query = select(ClothesRequest)
        if status_id is not None:
            query = query.where(ClothesRequest.status_id == status_id)
        if category_id is not None:
            query = query.where(ClothesRequest.category_id == category_id)
        result = await db.execute(query)
        requests = result.scalars().all()
        response = []
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

                ben_list.append({
                    "id": ben.id,
                    "person_name": ben.person_name,
                    "age_group": ben.age_group,
                    "gender_preference": ben.gender_preference,
                    "clothing_category_id": ben.clothing_category_id,
                    "need_by_date": ben.need_by_date,
                    "urgency_level_id": ben.urgency_level_id,
                    "verification_document_id": ben.verification_document_id,
                    "beneficiary_photo_id": ben.beneficiary_photo_id,
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
            response.append({
                "id": r.id,
                "user_id": r.user_id,
                "category_id": r.category_id,
                "request_title": r.request_title,
                "request_description": r.request_description,
                "status_id": r.status_id,
                "urgency_id": r.urgency_id,
                "beneficiaries": ben_list,
            })
        return response
    elif category_id in food_categories:
        # food_category_id: 1 = cooked, 2 = daily, 3 = grocery
        response = []
        if food_category_id == 1:
            cooked = await db.execute(cooked_food_q, {"status_id": status_id, "category_id": category_id})
            cooked_rows = cooked.fetchall()
            return {"food": {"cooked_food": [dict(row._mapping) for row in cooked_rows]}}
        elif food_category_id == 2:
            daily = await db.execute(daily_meal_q, {"status_id": status_id, "category_id": None, "food_request_category_id": category_id})
            daily_rows = daily.fetchall()
            return {"food": {"daily_meal": [dict(row._mapping) for row in daily_rows]}}
        elif food_category_id == 3:
            grocery = await db.execute(grocery_q, {"status_id": status_id, "category_id": None, "food_request_category_id": category_id})
            grocery_rows = grocery.fetchall()
            return {"food": {"grocery": [dict(row._mapping) for row in grocery_rows]}}
        else:
            cooked = await db.execute(cooked_food_q, {"status_id": status_id, "category_id": category_id})
            daily = await db.execute(daily_meal_q, {"status_id": status_id, "category_id": None, "food_request_category_id": category_id})
            grocery = await db.execute(grocery_q, {"status_id": status_id, "category_id": None, "food_request_category_id": category_id})
            cooked_rows = cooked.fetchall()
            daily_rows = daily.fetchall()
            grocery_rows = grocery.fetchall()
            return {
                "food": {
                    "cooked_food": [dict(row._mapping) for row in cooked_rows],
                    "daily_meal": [dict(row._mapping) for row in daily_rows],
                    "grocery": [dict(row._mapping) for row in grocery_rows]
                }
            }
    else:
        return []

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