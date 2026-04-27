from typing import Any, List, Optional

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
    prefix="/api/v1/education",
    tags=["Education Categories"],
    # dependencies=[Depends(get_current_user_id)],
)

@router.get("/support-documents", response_model=dict)
async def get__support_documents(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(EducationSupportDocument))
        support_documents = result.scalars().all()
        return success_response(data=[{"id": doc.id, "name": doc.name} for doc in support_documents], message="Fetched support documents")
    except Exception as e:
        logger.error(f"Error in get__support_documents: {e}")
        return error_response(message="Failed to fetch support documents", error=str(e))

@router.get("/support-types", response_model=dict)
async def get_support_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(EducationSupportType))
        support_types = result.scalars().all()
        return success_response(data=[{"id": st.id, "name": st.name} for st in support_types], message="Fetched support types")
    except Exception as e:
        logger.error(f"Error in get_support_types: {e}")
        return error_response(message="Failed to fetch support types", error=str(e))


@router.post("/education-request", response_model=dict)
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
            return error_response(message="Invalid user_id")

        if not await _exists(RequestCategory, payload.category_id):
            return error_response(message="Invalid category_id")

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
                return error_response(message=f"Invalid education_support_type_id at students[{i}]")

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
        return success_response(data={"request_id": new_request.id}, message="Education request created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_education_request: {e}")
        return error_response(message="Failed to create education request", error=str(e))
