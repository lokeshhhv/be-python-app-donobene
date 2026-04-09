from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.types import Attachment, RequestCategory, User
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
    # dependencies=[Depends(get_current_user_id)],
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


@router.post("/education-request")
async def create_education_request(
    payload: EducationRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:

        async def _exists(model, value: int):
            result = await db.execute(select(model.id).where(model.id == value))
            return result.scalar_one_or_none() is not None

        # ✅ validate
        if not await _exists(User, payload.user_id):
            raise HTTPException(400, "Invalid user_id")

        if not await _exists(RequestCategory, payload.category_id):
            raise HTTPException(400, "Invalid category_id")

        # ✅ create request
        new_request = EducationRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id,
            request_title=payload.request_title,
            request_description=payload.request_description
        )
        db.add(new_request)
        await db.flush()

        # ✅ students
        for i, stu in enumerate(payload.students, start=1):

            if not await _exists(EducationSupportType, stu.education_support_type_id):
                raise HTTPException(400, f"Invalid education_support_type_id at students[{i}]")

            verification_id = None
            support_doc_id = None

            # 🔥 verification attachment
            if stu.verification_document:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=stu.verification_document.document_type_id,
                    file_path=stu.verification_document.file_path
                )
                db.add(att)
                await db.flush()
                verification_id = att.id

            # 🔥 support doc attachment
            if stu.education_support_document:
                att = Attachment(
                    user_id=payload.user_id,
                    request_id=new_request.id,
                    category_id=payload.category_id,
                    document_type_id=stu.education_support_document.document_type_id,
                    file_path=stu.education_support_document.file_path
                )
                db.add(att)
                await db.flush()
                support_doc_id = att.id

            db.add(
                EducationRequestStudents(
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
                    verification_document_id=verification_id,
                    education_support_document_id=support_doc_id
                )
            )

        await db.commit()

        return {"message": "education request created successfully", "request_id": new_request.id}

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))

@router.get("/education-request", response_model=List[dict])
async def get_education_requests(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1️⃣ Fetch all education requests
        query = select(EducationRequest)
        if user_id is not None:
            query = query.where(EducationRequest.user_id == user_id)
        result = await db.execute(query)
        requests = result.scalars().all()

        response = []

        # 2️⃣ Loop through each request
        for r in requests:
            # Fetch all students for this request
            stu_result = await db.execute(
                select(EducationRequestStudents).where(
                    EducationRequestStudents.education_request_id == r.id
                )
            )
            students = stu_result.scalars().all()

            # Prepare student data
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

            # Append to final response
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))