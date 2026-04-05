from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.models.education import EducationRequest
from src.models.education import EducationRequestStudents
from src.models.education import EducationSupportDocument
from src.models.education import EducationSupportType
from src.schemas.EducationRequestPayload import EducationRequestPayload
from src.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Education Categories"],
    dependencies=[Depends(get_current_user_id)],
)

@router.get("/education-support-documents", response_model=list[dict])
async def get_education_support_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EducationSupportDocument))
    support_documents = result.scalars().all()
    return [
        {"id": doc.id, "name": doc.name} for doc in support_documents
    ]

@router.get("/education-support-types", response_model=list[dict])
async def get_education_support_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EducationSupportType))
    support_types = result.scalars().all()
    return [
        {"id": st.id, "name": st.name} for st in support_types
    ]


@router.post("/education-request", response_model=dict)
async def create_full_education_request(
    payload: EducationRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        # ✅ 1. Create main request
        new_request = EducationRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id,
            request_title=payload.request_title,
            request_description=payload.request_description
        )
        db.add(new_request)
        await db.flush()  # 🔥 get ID

        # ✅ 2. Loop students
        for stu in payload.students:
            new_student = EducationRequestStudents(
                education_request_id=new_request.id,
                person_name=stu.person_name,
                age=stu.age,
                grade_level=stu.grade_level,
                education_support_type_id=stu.education_support_type_id,
                amount_requested=stu.amount_requested,
                institution_name=stu.institution_name,
                college_id=stu.college_id,
                institution_address=stu.institution_address,
                contact_person_name=stu.contact_person_name,
                contact_person_phone=stu.contact_person_phone,
                verification_document_id=stu.verification_document_id,
                education_support_document_id=stu.education_support_document_id
            )
            db.add(new_student)

        # ✅ Final commit
        await db.commit()

        return {
            "message": "Education request created successfully",
            "request_id": new_request.id
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/education-request", response_model=list[dict])
async def get_all_education_requests(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(EducationRequest)

    if user_id is not None:
        query = query.where(EducationRequest.user_id == user_id)

    result = await db.execute(query)
    requests = result.scalars().all()

    response_data = []

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
                "education_request_id": s.education_request_id,
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
                "education_support_document_id": s.education_support_document_id,
            }
            for s in students
        ]

        response_data.append(
            {
                "id": r.id,
                "user_id": r.user_id,
                "category_id": r.category_id,
                "request_title": r.request_title,
                "request_description": r.request_description,
                "status_id": r.status_id,
                "urgency_id": r.urgency_id,
                "students": student_data,
            }
        )

    return response_data