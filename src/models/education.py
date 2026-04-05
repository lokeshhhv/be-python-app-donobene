from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from src.db.base import Base

class EducationRequest(Base):
    __tablename__ = "education_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("request_categories.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("request_status_master.id", ondelete="SET NULL"))
    urgency_id = Column(Integer, ForeignKey("urgency_levels.id", ondelete="SET NULL"))
    request_title = Column(String(255), nullable=False)
    request_description = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EducationRequestStudents(Base):
    __tablename__ = "education_request_students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    education_request_id = Column(Integer, ForeignKey("education_requests.id", ondelete="CASCADE"), nullable=False)
    person_name = Column(String(100))
    age = Column(Integer)
    grade_level = Column(String(50))
    education_support_type_id = Column(Integer, ForeignKey("education_support_types.id"), nullable=False)
    amount_requested = Column(Integer)
    institution_name = Column(String(255))
    college_id = Column(String(50))
    institution_address = Column(String(255))
    contact_person_name = Column(String(100))
    contact_person_phone = Column(String(15))
    verification_document_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))
    education_support_document_id = Column(Integer, ForeignKey("education_support_documents.id"), nullable=False)

class EducationSupportDocument(Base):
    __tablename__ = "education_support_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

class EducationSupportType(Base):
    __tablename__ = "education_support_types"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)