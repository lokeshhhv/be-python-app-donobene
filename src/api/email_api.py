from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from src.schemas.InvoiceRequest import InvoiceRequest
from src.utils.pdf_generator import PDFGenerator
from src.services.email_service import EmailService
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("email_api")


# Production HTML template with Jinja2 placeholders
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset=\"UTF-8\">
<style>
body{font-family: Arial, Helvetica, sans-serif;font-size:12px;margin:30px;color:#333;}
.watermark{position:fixed;top:40%;left:25%;font-size:110px;color:rgba(0,150,0,0.08);transform:rotate(-25deg);}
.header{display:flex;justify-content:space-between;align-items:center;border:1px solid #444;padding:15px;}
.company{font-size:14px;font-weight:bold;}
.invoice-title{font-size:14px;font-weight:bold;color:#2c4fa3;}
table{width:100%;border-collapse:collapse;}
th,td{border:1px solid #444;padding:8px;font-size:12px;}
.blue{background:#1d3f8b;color:white;font-weight:bold;}
.section{margin-top:10px;}
.label{color:#666;font-weight:bold;}
.tick{color:green;font-weight:bold;}
.footer{margin-top:20px;font-size:11px;color:#666;}
</style>
</head>
<body>
<div class=\"watermark\">✔ VERIFIED</div>
<div class=\"header\">
<div>
<div class=\"company\">DonoBene</div>
<div>Chennai, India</div>
<div>support@donobene.org</div>
</div>
<div class=\"invoice-title\">REQUEST INVOICE</div>
</div>
<table class=\"section\">
<tr>
<td class=\"label\">Request ID</td>
<td>{{ request_id }}</td>
<td class=\"label\">Submitted</td>
<td>{{ submitted_date }}</td>
</tr>
<tr>
<td class=\"label\">Type</td>
<td>{{ request_type }}</td>
<td class=\"label\">Urgency</td>
<td style=\"color:red\">{{ urgency }}</td>
</tr>
<tr>
<td class=\"label\">Verified</td>
<td class=\"tick\">{{ verified_status }}</td>
<td class=\"label\">Approved By</td>
<td>{{ approved_by }}</td>
</tr>
</table>
<table class=\"section\">
<tr class=\"blue\">
<th>#</th>
<th>Request Details</th>
<th>Status</th>
</tr>
<tr>
<td>1</td>
<td>{{ description }}</td>
<td>{{ status }}</td>
</tr>
</table>
<table class=\"section\">
<tr class=\"blue\">
<th colspan=\"2\">Receiver Profile</th>
</tr>
<tr>
<td class=\"label\">Name</td>
<td>{{ receiver_name }}</td>
</tr>
<tr>
<td class=\"label\">Receiver Type</td>
<td>{{ receiver_type }}</td>
</tr>
<tr>
<td class=\"label\">Address</td>
<td>{{ receiver_address }}</td>
</tr>
<tr>
<td class=\"label\">Last Request</td>
<td>{{ last_request }}</td>
</tr>
</table>
<table class=\"section\">
<tr>
<td style=\"height:80px\"></td>
<td style=\"height:80px\"></td>
</tr>
<tr>
<td align=\"center\">Authorized Signature<br>Date: {{ signature_date }}</td>
<td align=\"center\">Official Stamp</td>
</tr>
</table>
<div class=\"footer\">This document is system generated and verified by the organization.</div>
</body>
</html>
"""

@router.post("/send-invoice", status_code=status.HTTP_200_OK)
async def send_invoice(
    payload: InvoiceRequest,
    email_service: EmailService = Depends(EmailService)
):
    try:
        context = {
            "request_id": payload.request_id,
            "name": payload.name,
            "date": payload.invoice_date.strftime("%Y-%m-%d"),
            "amount": f"₹{payload.amount:,.2f}",
            "description": payload.description or "-",
            "submitted_date": payload.submitted_date,
            "request_type": payload.request_type,
            "urgency": payload.urgency,
            "verified_status": payload.verified_status,
            "approved_by": payload.approved_by,
            "status": payload.status,
            "receiver_type": payload.receiver_type,
            "receiver_address": payload.receiver_address,
            "last_request": payload.last_request,
            "signature_date": payload.signature_date,
            "receiver_name": payload.receiver_name
        }
        pdf_bytes = PDFGenerator.generate_pdf_from_html(HTML_TEMPLATE, context)
        subject = "Invoice of DonoBene"
        sender = "lokeshv5844@gmail.com"
        recipient = payload.email
        body = f"Dear {payload.name},\n\nPlease find attached your invoice.\n\nRegards,\nDonoBene Team"
        await email_service.send_email_with_attachment(
            subject=subject,
            sender=sender,
            recipient=recipient,
            body=body,
            attachment_bytes=pdf_bytes,
            attachment_filename=f"invoice_{payload.request_id}.pdf"
        )
        logger.info(f"Invoice sent to {recipient}")
        return JSONResponse(content={"message": "Invoice sent successfully."})
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))
