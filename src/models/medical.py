from sqlalchemy import Date, DECIMAL
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from src.db.base import Base

class HospitalDetails(Base):
    __tablename__ = "hospital_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))

    hospital_name = Column(String(255), nullable=False)
    hospital_address = Column(String(255))
    doctor_name = Column(String(100))

    financial_information = Column(String(50))
    amount_paid = Column(DECIMAL(10, 2))
    amount_requested = Column(DECIMAL(10, 2))
    funds_needed_by = Column(Date)

    contact_information = Column(String(255))
    emergency_contact_name = Column(String(255))

    attachment_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))
    prescription_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))
    estimation_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))

class MedicalRequestCategory(Base):
    __tablename__ = "medical_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)

class MedicalRequest(Base):
    __tablename__ = "medical_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("request_categories.id"), nullable=False)

    status_id = Column(Integer, ForeignKey("request_status_master.id", ondelete="SET NULL"))
    urgency_id = Column(Integer, ForeignKey("urgency_levels.id", ondelete="SET NULL"))

    request_title = Column(String(255), nullable=False)
    request_description = Column(Text)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MedicalSupportType(Base):
    __tablename__ = "support_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)

class PatientSupportType(Base):
    __tablename__ = "patient_support_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))
    support_type_id = Column(Integer, ForeignKey("support_types.id"))

class BloodGroup(Base):
    __tablename__ = "blood_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medical_request_id = Column(Integer, ForeignKey("medical_requests.id", ondelete="CASCADE"))

    patient_name = Column(String(100), nullable=False)
    age = Column(Integer)

    gender_id = Column(Integer, ForeignKey("gender.id"))
    medical_condition = Column(String(255))

    blood_group_id = Column(Integer, ForeignKey("blood_groups.id"))
    medical_category_id = Column(Integer, ForeignKey("medical_categories.id"))
