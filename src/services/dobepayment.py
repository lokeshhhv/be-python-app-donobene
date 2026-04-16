import datetime
import razorpay
from src.models.dobepayment import DonationEvent

import hmac
import hashlib
import os

def generate_receipt(donation_id):
    year = datetime.datetime.now().year
    return f"DON-{year}-{str(donation_id).zfill(6)}"



async def log_event(db, donation_id, event_type, data=None):
    event = DonationEvent(
        donation_id=donation_id,
        event_type=event_type,
        event_data=data
    )
    db.add(event)
    await db.commit()

client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))

def create_order(amount, receipt):
    return client.order.create({
        "amount": amount,
        "currency": "INR",
        "receipt": receipt
    })

def verify_signature(order_id, payment_id, signature):

    body = f"{order_id}|{payment_id}"

    generated_signature = hmac.new(
        bytes(os.getenv("RAZORPAY_KEY_SECRET"), "utf-8"),
        bytes(body, "utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(generated_signature, signature)