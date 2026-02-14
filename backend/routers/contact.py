"""Public contact form endpoint."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, Request

from dependencies import get_db
from email_service import email_service
from config import settings

router = APIRouter(prefix="/contact", tags=["contact"])


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    company: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    subject: str = Field(..., min_length=3, max_length=160)
    message: str = Field(..., min_length=10, max_length=4000)


@router.post("")
async def submit_contact_form(payload: ContactRequest, request: Request, db=Depends(get_db)):
    # basic anti-abuse guard
    if len(payload.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Message is too short")

    contact_collection = db.get_collection("contact_submissions")
    doc = {
        "name": payload.name.strip(),
        "email": payload.email.lower(),
        "company": (payload.company or "").strip() or None,
        "phone": (payload.phone or "").strip() or None,
        "subject": payload.subject.strip(),
        "message": payload.message.strip(),
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "created_at": datetime.utcnow(),
        "status": "new",
    }

    await contact_collection.insert_one(doc)

    support_email = settings.public_support_email or settings.email_from or "support@cryptovault.financial"
    try:
        await email_service.send_email(
            to_email=support_email,
            subject=f"[Contact] {doc['subject']}",
            html_content=(
                f"<h3>New contact form submission</h3>"
                f"<p><b>Name:</b> {doc['name']}</p>"
                f"<p><b>Email:</b> {doc['email']}</p>"
                f"<p><b>Company:</b> {doc['company'] or '-'} </p>"
                f"<p><b>Phone:</b> {doc['phone'] or '-'} </p>"
                f"<p><b>Message:</b><br>{doc['message']}</p>"
            ),
            text_content=(
                f"New contact form submission\n"
                f"Name: {doc['name']}\n"
                f"Email: {doc['email']}\n"
                f"Company: {doc['company'] or '-'}\n"
                f"Phone: {doc['phone'] or '-'}\n"
                f"Message:\n{doc['message']}"
            ),
        )
    except Exception:
        # Non-blocking for end-user flow
        pass

    return {"success": True, "message": "Thanks for contacting us. Our team will get back to you soon."}
