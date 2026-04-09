from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Text, func
from src.db.base import Base


class ShelterDurationOptions(Base):
    __tablename__ = "shelter_duration_options"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)

class ShelterRequest(Base):
    __tablename__ = "shelter_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("request_categories.id"), nullable=False)

    request_title = Column(String(255), nullable=False)
    request_description = Column(Text)

    status_id = Column(Integer, ForeignKey("request_status_master.id", ondelete="SET NULL"))
    urgency_id = Column(Integer, ForeignKey("urgency_levels.id", ondelete="SET NULL"))

    verified = Column(Boolean, default=False)
    reject_reason = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ShelterBeneficiary(Base):
    __tablename__ = "shelter_beneficiaries"

    id = Column(Integer, primary_key=True, autoincrement=True)

    shelter_request_id = Column(Integer, ForeignKey("shelter_requests.id", ondelete="CASCADE"), nullable=False)

    person_name = Column(String(100))
    total_members = Column(Integer)

    special_need_id = Column(Integer, ForeignKey("shelter_special_needs.id", ondelete="SET NULL"))
    staying_type_id = Column(Integer, ForeignKey("shelter_staying_types.id", ondelete="SET NULL"))

    current_address = Column(String(255))
    duration_of_problem = Column(String(50))

    requirement_type_id = Column(Integer, ForeignKey("shelter_requirement_types.id", ondelete="SET NULL"))
    duration_option_id = Column(Integer, ForeignKey("shelter_duration_options.id", ondelete="SET NULL"))

    number_of_days = Column(Integer)

    verification_document_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))
    damage_document_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))


class ShelterRequirementTypes(Base):
    __tablename__ = "shelter_requirement_types"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)

class ShelterSpecialNeeds(Base):
    __tablename__ = "shelter_special_needs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)

class ShelterStayingTypes(Base):
    __tablename__ = "shelter_staying_types"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)