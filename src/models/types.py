from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from src.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    type_donor_id = Column(Integer, ForeignKey("type_donors.id"), nullable=True)
    donor_type_subtype = Column(Integer, ForeignKey("user_types.id"), nullable=True)
    organization_name = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    attachment_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_profile_update = Column(DateTime(timezone=True), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

class UserType(Base):
    __tablename__ = "user_types"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

class UrgencyLevel(Base):
    __tablename__ = "urgency_levels"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

class SwitchUser(Base):
    __tablename__ = 'switch_users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    switched_to_type = Column(Integer, ForeignKey("type_donors.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    switched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class RequestCategory(Base):
    __tablename__ = "request_categories"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(String(50), nullable=False, unique=True)
    category_type = Column(String(100), nullable=False, comment="e.g., Food, Clothes, Education, etc.")

class RequestStatusMaster(Base):
    __tablename__ = "request_status_master"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)

class Gender(Base):
    __tablename__ = 'gender'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gender_name = Column(String(50), unique=True, nullable=False, comment='e.g., Male, Female, Other')

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)

    document_type_id = Column(Integer, nullable=False)
    file_path = Column(String(255), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

class TypeDonor(Base):
    __tablename__ = "type_donors"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
