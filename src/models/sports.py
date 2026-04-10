from sqlalchemy import JSON, Boolean, Column, Integer, String, ForeignKey, DateTime, Date, Text, func
from src.db.base import Base

class SportsCategory(Base):
    __tablename__ = "sports_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)


class SportsSupportType(Base):
    __tablename__ = "sports_support_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)


class PlayingLevel(Base):
    __tablename__ = "playing_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)


class SportsRequest(Base):
    __tablename__ = "sports_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("request_categories.id"), nullable=False)

    request_title = Column(String(255), nullable=False)
    request_description = Column(Text)

    verified = Column(Boolean, default=False)
    reject_reason = Column(Text)

    urgency_id = Column(Integer, ForeignKey("urgency_levels.id"))
    status_id = Column(Integer, ForeignKey("request_status_master.id"))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())



class SportsRequestBeneficiary(Base):
    __tablename__ = "sports_request_beneficiaries"

    id = Column(Integer, primary_key=True, autoincrement=True)

    sports_request_id = Column(Integer, ForeignKey("sports_requests.id", ondelete="CASCADE"), nullable=False)

    person_name = Column(String(100))
    age_group = Column(String(50))
    gender_id = Column(Integer, ForeignKey("gender.id"))

    playing_level_id = Column(Integer, ForeignKey("playing_levels.id"), nullable=False)

    achievement = Column(String(255))
    amount_requested = Column(Integer)
    event_date = Column(Date)

    institution_name = Column(String(255))
    phone = Column(String(15))

    verification_document_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))
    achievement_document_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"))


    sports_category_ids = Column(JSON)
    support_type_ids = Column(JSON)