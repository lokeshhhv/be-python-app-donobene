import hmac
import hashlib

# Replace with your actual webhook secret
webhook_secret = "YOUR_WEBHOOK_SECRET"

# Paste your exact JSON payload here (as a single line, no extra spaces or newlines)
body = '''{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_test123456",
        "order_id": "order_SeDXp72XNt9jwy",
        "amount": 5000,
        "currency": "INR",
        "status": "captured"
      }
    }
  }
}'''.strip()

signature = hmac.new(
    webhook_secret.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

print("X-Razorpay-Signature:", signature)
