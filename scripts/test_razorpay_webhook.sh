#!/bin/bash

# Set your webhook secret here
WEBHOOK_SECRET="test_webhook_secret_123"


# Accept dynamic values as arguments
PAYMENT_ID="$1"
ORDER_ID="$2"
AMOUNT="$3"
CURRENCY="${4:-INR}"
STATUS="${5:-captured}"

if [[ -z "$PAYMENT_ID" || -z "$ORDER_ID" || -z "$AMOUNT" ]]; then
  echo "Usage: $0 <payment_id> <order_id> <amount> [currency] [status]"
  exit 1
fi

PAYLOAD="{\"event\":\"payment.captured\",\"payload\":{\"payment\":{\"entity\":{\"id\":\"$PAYMENT_ID\",\"order_id\":\"$ORDER_ID\",\"amount\":$AMOUNT,\"currency\":\"$CURRENCY\",\"status\":\"$STATUS\"}}}}"

# Generate signature
SIGNATURE=$(python3 -c "import hmac,hashlib; print(hmac.new(b'$WEBHOOK_SECRET', b'$PAYLOAD', hashlib.sha256).hexdigest())")

# Print info
echo "========================================"
echo "Webhook Secret: $WEBHOOK_SECRET"
echo "========================================"
echo ""
echo "JSON Payload:"
echo "$PAYLOAD" | python3 -m json.tool
echo ""
echo "Generated Signature: $SIGNATURE"
echo ""
echo "========================================"
echo "CURL COMMAND:"
echo "========================================"
echo "curl -X POST http://127.0.0.1:8000/api/v1/dobepayment/webhook/razorpay \
  -H 'Content-Type: application/json' \
  -H 'X-Razorpay-Signature: $SIGNATURE' \
  -d '$PAYLOAD'"
echo ""
echo "========================================"
echo "API RESPONSE:"
echo "========================================"
curl -X POST http://127.0.0.1:8000/api/v1/dobepayment/webhook/razorpay \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: $SIGNATURE" \
  -d "$PAYLOAD" -w "\n\nHTTP Status: %{http_code}\n"
