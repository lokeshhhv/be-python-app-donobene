from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.sql import func
from src.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging
# --- Webhook Event Model ---
from sqlalchemy.orm import declarative_base
Base = declarative_base()
class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50))
    payload = Column(JSON)
    received_at = Column(TIMESTAMP, server_default=func.now())
from pydantic import BaseModel
from typing import Dict, Any
# --- Razorpay Webhook Models ---
class RazorpayPaymentEntity(BaseModel):
    id: str
    order_id: str
    amount: int
    currency: str
    status: str

class RazorpayPaymentPayload(BaseModel):
    entity: RazorpayPaymentEntity

class RazorpayWebhookPayload(BaseModel):
    event: str
    payload: Dict[str, RazorpayPaymentPayload]
import json

from fastapi import APIRouter, Depends, Request, status, HTTPException
from src.schemas.DonationRequest import DonationRequest
from src.schemas.VerifyRequest import VerifyRequest
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.dobepayment import Donation, Payment
from src.models.types import User
from src.services.dobepayment import create_order, generate_receipt, log_event, verify_signature
from src.db.session import get_db
from src.core.dependencies import get_current_user_id


import hmac
import hashlib
import os


router = APIRouter(
    prefix="/api/v1/dobepayment",
    tags=["Dobe Payment"],
    # dependencies=[Depends(get_current_user_id)],
)

@router.post("/donate")
async def create_donation(data: DonationRequest, db: AsyncSession = Depends(get_db)):
    donation = Donation(
        user_id=None,
        donor_name=data.name,
        donor_email=data.email,
        donor_phone=data.phone,
        amount=data.amount,
        payment_method="RAZORPAY"
    )
    db.add(donation)
    await db.commit()
    await db.refresh(donation)

    donation.receipt_number = generate_receipt(donation.id)

    order = create_order(int(data.amount * 100), str(donation.id))

    payment = Payment(
        donation_id=donation.id,
        provider="RAZORPAY",
        provider_order_id=order["id"],
        amount=data.amount,
        status="CREATED"
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    print(f"[DEBUG] Payment inserted with provider_order_id: {order['id']}")

    await log_event(db, donation.id, "ORDER_CREATED")

    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key": os.getenv("RAZORPAY_KEY_ID")
    }

@router.post("/verify")
async def verify_payment(data: VerifyRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).filter_by(provider_order_id=data.order_id))
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(404, "Order not found")

    result = await db.execute(select(Donation).filter_by(id=payment.donation_id))
    donation = result.scalars().first()

    # signature verify
    if not verify_signature(
        data.order_id,
        data.payment_id,
        data.signature
    ):
        raise HTTPException(400, "Invalid signature")

    # idempotent check
    if donation.status == "PAID":
        return {"message": "Already paid"}

    # amount check
    if float(payment.amount) != float(donation.amount):
        raise HTTPException(400, "Amount mismatch")

    donation.status = "PAID"
    payment.provider_payment_id = data.payment_id
    payment.status = "CAPTURED"

    await db.commit()

    log_event(db, donation.id, "PAYMENT_SUCCESS")

    return {"status": "success"}


@router.post("/webhook/razorpay", response_model=Dict[str, Any])
async def webhook(
    payload: RazorpayWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    # Log every webhook call
    logging.info(f"Webhook received: {body}")
    # Store full payload for auditing
    try:
        event_type = payload.event
        webhook_event = PaymentWebhookEvent(event_type=event_type, payload=payload.dict())
        db.add(webhook_event)
        await db.commit()
    except Exception as e:
        logging.error(f"Failed to store webhook event: {e}")

    # Signature check
    if not signature or not webhook_secret:
        logging.warning("Missing signature or webhook secret")
        return {"ok": False, "detail": "Missing signature or webhook secret"}

    generated_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(generated_signature, signature):
        logging.warning("Invalid webhook signature")
        return {"ok": False, "detail": "Invalid webhook signature"}

    try:
        event = payload.event
        payment_data = payload.payload["payment"].entity
        order_id = payment_data.order_id

        result = await db.execute(select(Payment).filter_by(provider_order_id=order_id))
        payment = result.scalars().first()
        if not payment:
            return {"ok": True}

        result = await db.execute(select(Donation).filter_by(id=payment.donation_id))
        donation = result.scalars().first()

        if event == "payment.captured":
            if donation.status != "PAID":
                donation.status = "PAID"
                payment.status = "CAPTURED"
                await log_event(db, donation.id, "WEBHOOK_CONFIRMED")
        elif event == "payment.failed":
            donation.status = "FAILED"
            payment.status = "FAILED"
            await log_event(db, donation.id, "PAYMENT_FAILED")

        await db.commit()
        await db.refresh(payment)
        await db.refresh(donation)
        logging.info(f"[WEBHOOK] Updated Payment: id={payment.id}, status={payment.status}, provider_order_id={payment.provider_order_id}, provider_payment_id={payment.provider_payment_id}")
        logging.info(f"[WEBHOOK] Updated Donation: id={donation.id}, status={donation.status}, amount={donation.amount}, donor={donation.donor_name}")
        return {"ok": True}
    except Exception as e:
        logging.error(f"Webhook processing error: {e}")
        return {"ok": False, "detail": str(e)}