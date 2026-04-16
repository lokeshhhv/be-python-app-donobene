from sqlalchemy import JSON, Column, Integer, String, Enum, DECIMAL, ForeignKey, Text, TIMESTAMP
from sqlalchemy.sql import func
from src.db import Base

class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    donor_name = Column(String(100), nullable=False)
    donor_email = Column(String(150), nullable=False)
    donor_phone = Column(String(15), nullable=False)

    amount = Column(DECIMAL(10,2), nullable=False)
    currency = Column(String(10), default="INR")

    payment_method = Column(Enum("RAZORPAY","QR"), nullable=False)

    status = Column(Enum(
        "CREATED","PAYMENT_PENDING","PAID","FAILED","VERIFIED","REJECTED"
    ), default="CREATED")

    receipt_number = Column(String(50), unique=True)

    note = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)

    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"))

    provider = Column(Enum("RAZORPAY","QR"))

    provider_order_id = Column(String(100), unique=True)
    provider_payment_id = Column(String(100), unique=True)

    amount = Column(DECIMAL(10,2), nullable=False)
    currency = Column(String(10))

    status = Column(Enum("CREATED","AUTHORIZED","CAPTURED","FAILED"))

    method = Column(String(50))

    raw_response = Column(JSON)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DonationEvent(Base):
    __tablename__ = "donation_events"

    id = Column(Integer, primary_key=True)

    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"))

    event_type = Column(Enum(
        "CREATED","ORDER_CREATED","PAYMENT_SUCCESS",
        "PAYMENT_FAILED","WEBHOOK_CONFIRMED",
        "QR_SUBMITTED","VERIFIED","REJECTED"
    ))

    event_data = Column(JSON)

    created_at = Column(TIMESTAMP, server_default=func.now())

class QRPayment(Base):
    __tablename__ = "qr_payments"

    id = Column(Integer, primary_key=True)

    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"))

    transaction_ref = Column(String(150))
    screenshot_attachment_id = Column(Integer, ForeignKey("attachments.id"))

    status = Column(Enum("PENDING","APPROVED","REJECTED"), default="PENDING")

    verified_by = Column(Integer, ForeignKey("users.id"))
    verified_at = Column(TIMESTAMP)

    created_at = Column(TIMESTAMP, server_default=func.now())