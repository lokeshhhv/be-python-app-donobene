from sqlalchemy import DECIMAL, Column, Integer, String, ForeignKey, DateTime, func
from src.db.base import Base

class ClothesRequest(Base):
    __tablename__ = "clothes_requests"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("request_categories.id"), nullable=False)
    request_title = Column(String(255), nullable=False)
    request_description = Column(String)
    status_id = Column(Integer, ForeignKey("request_status_master.id", ondelete="SET NULL"))
    urgency_id = Column(Integer, ForeignKey("urgency_levels.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ClothesRequestBeneficiaries(Base):
    __tablename__ = "clothes_beneficiaries"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    clothes_request_id = Column(Integer, ForeignKey("clothes_requests.id", ondelete="CASCADE"), nullable=False)
    person_name = Column(String(100))
    age_group = Column(Integer, ForeignKey("clothes_age_groups.id"))
    gender_preference = Column(Integer, ForeignKey("gender.id"), nullable=False)
    clothing_category_id = Column(Integer, ForeignKey("clothing_categories.id"), nullable=False)
    need_by_date = Column(DateTime)
    urgency_level_id = Column(Integer, ForeignKey("urgency_levels.id"))
    verification_document_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"), nullable=True)
    beneficiary_photo_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"), nullable=True)
    amount_requested = Column(DECIMAL(10, 2))

class ClothesRequestBeneficiariesSizes(Base):
    __tablename__ = "beneficiary_clothing_sizes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    beneficiary_id = Column(Integer, ForeignKey("clothes_beneficiaries.id", ondelete="CASCADE"), nullable=False)
    clothing_type = Column(String(100), nullable=False)
    size_id = Column(Integer, ForeignKey("clothing_size_row.id"), nullable=False)
    quantity = Column(Integer, default=0)

class ClothingCategory(Base):
    __tablename__ = "clothing_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

class ClothingSizeRow(Base):
    __tablename__ = "clothing_size_row"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

class ClothesAgeGroup(Base):
    __tablename__ = "clothes_age_groups"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

