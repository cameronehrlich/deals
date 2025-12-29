"""
Contacts API routes.

Phase 5.2: Contact & Outreach
- Contact management tied to properties
- Communication timeline/log
- Email templates with property variable substitution
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.db.models import (
    ContactDB, CommunicationDB, get_session, get_engine
)

router = APIRouter()


# ==================== Pydantic Models ====================

class ContactBase(BaseModel):
    """Base contact fields."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    contact_type: Optional[str] = None  # listing_agent, buyer_agent, seller, lender, other
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    """Create a new contact."""
    property_ids: Optional[List[str]] = []
    agent_id: Optional[str] = None
    agent_photo_url: Optional[str] = None
    agent_profile_data: Optional[dict] = None


class ContactUpdate(BaseModel):
    """Update contact fields (all optional)."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    contact_type: Optional[str] = None
    notes: Optional[str] = None
    property_ids: Optional[List[str]] = None
    next_followup: Optional[datetime] = None


class ContactResponse(ContactBase):
    """Contact response."""
    id: str
    property_ids: List[str]
    agent_id: Optional[str] = None
    agent_photo_url: Optional[str] = None
    agent_profile_data: Optional[dict] = None
    last_contacted: Optional[datetime] = None
    next_followup: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommunicationBase(BaseModel):
    """Base communication fields."""
    comm_type: str  # email, call, text, meeting, note
    direction: Optional[str] = None  # inbound, outbound, internal
    subject: Optional[str] = None
    content: Optional[str] = None


class CommunicationCreate(CommunicationBase):
    """Create a new communication."""
    contact_id: str
    property_id: Optional[str] = None
    template_used: Optional[str] = None
    occurred_at: Optional[datetime] = None


class CommunicationResponse(CommunicationBase):
    """Communication response."""
    id: str
    contact_id: str
    property_id: Optional[str] = None
    template_used: Optional[str] = None
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Email Templates ====================

# Built-in email templates with variable substitution
EMAIL_TEMPLATES = {
    "initial_inquiry": {
        "name": "Initial Inquiry",
        "description": "First contact with listing agent about a property",
        "subject": "Inquiry about {address}",
        "body": """Hi {agent_name},

I'm writing to express interest in the property at {address}, listed at {list_price}.

I'm an active investor looking for rental properties in the {city} area. I have a few questions:

1. Is this property still available?
2. Is the seller motivated? Are there any competing offers?
3. Can you share the rent roll or lease details if tenant-occupied?
4. Are there any known issues or recent repairs?

I'm pre-qualified for financing and can move quickly on the right property. Would you have time for a call this week to discuss?

Best regards,
{sender_name}
{sender_phone}
{sender_email}""",
    },
    "follow_up_day1": {
        "name": "Follow-up (Day 1)",
        "description": "First follow-up after initial contact",
        "subject": "Following up: {address}",
        "body": """Hi {agent_name},

I wanted to follow up on my inquiry about {address}. I'm very interested in this property and would love to schedule a showing or discuss further.

Do you have availability this week?

Thanks,
{sender_name}
{sender_phone}""",
    },
    "follow_up_day3": {
        "name": "Follow-up (Day 3)",
        "description": "Second follow-up",
        "subject": "Re: {address} - Still interested",
        "body": """Hi {agent_name},

Just checking in again on {address}. Is this property still available? I'd like to move forward if so.

Please let me know the best way to reach you.

{sender_name}
{sender_phone}""",
    },
    "follow_up_day7": {
        "name": "Follow-up (Day 7)",
        "description": "Final follow-up before moving on",
        "subject": "Last check-in: {address}",
        "body": """Hi {agent_name},

I've reached out a few times about {address} but haven't heard back. If this property is no longer available or there's another reason you haven't responded, no worries at all.

If you do have other investment properties coming up in {city}, I'd love to be on your list for future opportunities.

Best,
{sender_name}
{sender_email}""",
    },
    "request_disclosures": {
        "name": "Request Disclosures",
        "description": "Request seller disclosures and property documents",
        "subject": "Document request: {address}",
        "body": """Hi {agent_name},

Before moving forward with an offer on {address}, I'd like to request the following documents:

- Seller disclosures
- Property inspection reports (if available)
- Rent roll / lease agreements (if tenant-occupied)
- HOA documents and financials (if applicable)
- Recent utility bills (last 12 months if available)
- Any repair/maintenance records

Please let me know the best way to receive these documents.

Thank you,
{sender_name}
{sender_email}""",
    },
    "offer_submission": {
        "name": "Offer Submission",
        "description": "Cover letter for submitting an offer",
        "subject": "Offer submitted: {address}",
        "body": """Hi {agent_name},

Please find attached my offer for {address}.

Offer Summary:
- Offer Price: {offer_price}
- Down Payment: {down_payment_pct}%
- Earnest Money: {earnest_money}
- Closing Timeline: {closing_days} days
- Contingencies: {contingencies}

I'm a serious buyer with financing in place and can close on schedule. Please let me know if you have any questions or if the seller would like to counter.

I look forward to your response.

Best regards,
{sender_name}
{sender_phone}
{sender_email}""",
    },
    "fsbo_outreach": {
        "name": "FSBO Outreach",
        "description": "Contacting For Sale By Owner properties",
        "subject": "Interested in your property at {address}",
        "body": """Hello,

I came across your property at {address} and I'm interested in learning more.

I'm a real estate investor looking for rental properties in {city}. I buy properties directly and can offer:

- Quick closing (as fast as 2-3 weeks)
- Cash or conventional financing
- Flexibility on timing
- No agent commissions on your side

Would you be open to a brief call to discuss the property and your goals for the sale?

Best regards,
{sender_name}
{sender_phone}
{sender_email}""",
    },
}


class EmailTemplateResponse(BaseModel):
    """Email template response."""
    id: str
    name: str
    description: str
    subject: str
    body: str
    variables: List[str]


class GenerateEmailRequest(BaseModel):
    """Request to generate an email from a template."""
    template_id: str
    variables: dict  # Variable values to substitute


class GenerateEmailResponse(BaseModel):
    """Generated email response."""
    subject: str
    body: str


# ==================== Contact Routes ====================

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    contact_type: Optional[str] = None,
    property_id: Optional[str] = None,
    search: Optional[str] = None,
    has_followup: Optional[bool] = None,
):
    """Get all contacts with optional filtering."""
    session = get_session(get_engine())
    try:
        query = session.query(ContactDB)

        if contact_type:
            query = query.filter(ContactDB.contact_type == contact_type)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (ContactDB.name.ilike(search_term)) |
                (ContactDB.email.ilike(search_term)) |
                (ContactDB.company.ilike(search_term))
            )

        if has_followup is not None:
            if has_followup:
                query = query.filter(ContactDB.next_followup.isnot(None))
            else:
                query = query.filter(ContactDB.next_followup.is_(None))

        contacts = query.order_by(ContactDB.updated_at.desc()).all()

        # Filter by property_id in Python (JSON column)
        if property_id:
            contacts = [c for c in contacts if property_id in (c.property_ids or [])]

        return [ContactResponse.model_validate(c) for c in contacts]
    finally:
        session.close()


@router.post("/", response_model=ContactResponse)
async def create_contact(data: ContactCreate):
    """Create a new contact."""
    session = get_session(get_engine())
    try:
        contact = ContactDB(
            name=data.name,
            email=data.email,
            phone=data.phone,
            company=data.company,
            contact_type=data.contact_type,
            notes=data.notes,
            property_ids=data.property_ids or [],
            agent_id=data.agent_id,
            agent_photo_url=data.agent_photo_url,
            agent_profile_data=data.agent_profile_data,
        )
        session.add(contact)
        session.commit()
        session.refresh(contact)
        return ContactResponse.model_validate(contact)
    finally:
        session.close()


# ==================== Communication Routes ====================

@router.get("/communications", response_model=List[CommunicationResponse])
async def get_communications(
    contact_id: Optional[str] = None,
    property_id: Optional[str] = None,
    comm_type: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    """Get communications with optional filtering."""
    session = get_session(get_engine())
    try:
        query = session.query(CommunicationDB)

        if contact_id:
            query = query.filter(CommunicationDB.contact_id == contact_id)

        if property_id:
            query = query.filter(CommunicationDB.property_id == property_id)

        if comm_type:
            query = query.filter(CommunicationDB.comm_type == comm_type)

        comms = query.order_by(CommunicationDB.occurred_at.desc()).limit(limit).all()
        return [CommunicationResponse.model_validate(c) for c in comms]
    finally:
        session.close()


@router.post("/communications", response_model=CommunicationResponse)
async def create_communication(data: CommunicationCreate):
    """Log a new communication."""
    session = get_session(get_engine())
    try:
        # Verify contact exists
        contact = session.query(ContactDB).filter(ContactDB.id == data.contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        comm = CommunicationDB(
            contact_id=data.contact_id,
            property_id=data.property_id,
            comm_type=data.comm_type,
            direction=data.direction,
            subject=data.subject,
            content=data.content,
            template_used=data.template_used,
            occurred_at=data.occurred_at or datetime.utcnow(),
        )
        session.add(comm)

        # Update contact's last_contacted
        contact.last_contacted = comm.occurred_at
        contact.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(comm)
        return CommunicationResponse.model_validate(comm)
    finally:
        session.close()


@router.delete("/communications/{comm_id}")
async def delete_communication(comm_id: str):
    """Delete a communication."""
    session = get_session(get_engine())
    try:
        comm = session.query(CommunicationDB).filter(CommunicationDB.id == comm_id).first()
        if not comm:
            raise HTTPException(status_code=404, detail="Communication not found")

        session.delete(comm)
        session.commit()
        return {"success": True}
    finally:
        session.close()


# ==================== Email Template Routes ====================

@router.get("/templates", response_model=List[EmailTemplateResponse])
async def get_email_templates():
    """Get all email templates."""
    templates = []
    for template_id, template in EMAIL_TEMPLATES.items():
        # Extract variables from template
        import re
        variables = list(set(re.findall(r'\{(\w+)\}', template["subject"] + template["body"])))
        templates.append(EmailTemplateResponse(
            id=template_id,
            name=template["name"],
            description=template["description"],
            subject=template["subject"],
            body=template["body"],
            variables=sorted(variables),
        ))
    return templates


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(template_id: str):
    """Get a specific email template."""
    if template_id not in EMAIL_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = EMAIL_TEMPLATES[template_id]
    import re
    variables = list(set(re.findall(r'\{(\w+)\}', template["subject"] + template["body"])))

    return EmailTemplateResponse(
        id=template_id,
        name=template["name"],
        description=template["description"],
        subject=template["subject"],
        body=template["body"],
        variables=sorted(variables),
    )


@router.post("/templates/{template_id}/generate", response_model=GenerateEmailResponse)
async def generate_email(template_id: str, request: GenerateEmailRequest):
    """Generate an email from a template with variable substitution."""
    if template_id not in EMAIL_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = EMAIL_TEMPLATES[template_id]

    # Replace variables
    subject = template["subject"]
    body = template["body"]

    for key, value in request.variables.items():
        placeholder = "{" + key + "}"
        subject = subject.replace(placeholder, str(value) if value else "")
        body = body.replace(placeholder, str(value) if value else "")

    return GenerateEmailResponse(subject=subject, body=body)


# ==================== Property Contact Timeline ====================

@router.get("/properties/{property_id}/timeline")
async def get_property_timeline(property_id: str):
    """Get the full communication timeline for a property."""
    session = get_session(get_engine())
    try:
        # Get all communications for this property
        comms = session.query(CommunicationDB).filter(
            CommunicationDB.property_id == property_id
        ).order_by(CommunicationDB.occurred_at.desc()).all()

        # Get all contacts linked to this property
        contacts = session.query(ContactDB).all()
        linked_contacts = [c for c in contacts if property_id in (c.property_ids or [])]

        return {
            "property_id": property_id,
            "contacts": [ContactResponse.model_validate(c) for c in linked_contacts],
            "communications": [CommunicationResponse.model_validate(c) for c in comms],
            "total_contacts": len(linked_contacts),
            "total_communications": len(comms),
        }
    finally:
        session.close()


# ==================== Contact ID Routes ====================
# These are at the end to avoid /{contact_id} matching paths like /templates

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: str):
    """Get a specific contact."""
    session = get_session(get_engine())
    try:
        contact = session.query(ContactDB).filter(ContactDB.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return ContactResponse.model_validate(contact)
    finally:
        session.close()


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: str, data: ContactUpdate):
    """Update a contact."""
    session = get_session(get_engine())
    try:
        contact = session.query(ContactDB).filter(ContactDB.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)

        contact.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(contact)
        return ContactResponse.model_validate(contact)
    finally:
        session.close()


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact."""
    session = get_session(get_engine())
    try:
        contact = session.query(ContactDB).filter(ContactDB.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        # Also delete associated communications
        session.query(CommunicationDB).filter(
            CommunicationDB.contact_id == contact_id
        ).delete()

        session.delete(contact)
        session.commit()
        return {"success": True, "message": f"Deleted contact: {contact.name}"}
    finally:
        session.close()


@router.post("/{contact_id}/link-property", response_model=ContactResponse)
async def link_property_to_contact(contact_id: str, property_id: str):
    """Link a property to a contact."""
    session = get_session(get_engine())
    try:
        contact = session.query(ContactDB).filter(ContactDB.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        property_ids = contact.property_ids or []
        if property_id not in property_ids:
            property_ids.append(property_id)
            contact.property_ids = property_ids
            contact.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(contact)

        return ContactResponse.model_validate(contact)
    finally:
        session.close()


@router.post("/{contact_id}/unlink-property", response_model=ContactResponse)
async def unlink_property_from_contact(contact_id: str, property_id: str):
    """Unlink a property from a contact."""
    session = get_session(get_engine())
    try:
        contact = session.query(ContactDB).filter(ContactDB.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        property_ids = contact.property_ids or []
        if property_id in property_ids:
            property_ids.remove(property_id)
            contact.property_ids = property_ids
            contact.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(contact)

        return ContactResponse.model_validate(contact)
    finally:
        session.close()
