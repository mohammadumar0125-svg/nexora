
from app.core.database import get_unscoped_db
from app.core.deps import extract_client_ip
from app.core.rate_limit import check_api_rate_limit
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(prefix="/public", tags=["Public"])


class EarlyAccessIn(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., min_length=5, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)
    business_type: str = Field(default="SME", max_length=120)
    team_size: str = Field(default="6-25", max_length=40)
    notes: str = Field(default="", max_length=2000)


class ContactIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., min_length=5, max_length=255)
    company: str = Field(default="", max_length=255)
    topic: str = Field(default="General", max_length=120)
    message: str = Field(..., min_length=5, max_length=3000)


@router.post("/early-access", status_code=status.HTTP_201_CREATED)
def submit_early_access(
    payload: EarlyAccessIn,
    request: Request,
    db: Session = Depends(get_unscoped_db),
):
    check_api_rate_limit(f"public_ea:{extract_client_ip(request)}", max_requests=12, window_seconds=60)
    row = db.execute(
        text(
            """
            INSERT INTO public_early_access_requests (full_name, email, company_name, business_type, team_size, notes)
            VALUES (:fn, :em, :cn, :bt, :ts, :nt)
            RETURNING id::text, created_at
            """
        ),
        {
            "fn": payload.full_name.strip(),
            "em": payload.email.strip().lower(),
            "cn": payload.company_name.strip(),
            "bt": payload.business_type.strip(),
            "ts": payload.team_size.strip(),
            "nt": payload.notes.strip(),
        },
    ).mappings().first()
    db.commit()
    return {"id": row["id"], "status": "recorded", "created_at": row["created_at"]}


@router.post("/contact", status_code=status.HTTP_201_CREATED)
def submit_contact(
    payload: ContactIn,
    request: Request,
    db: Session = Depends(get_unscoped_db),
):
    check_api_rate_limit(f"public_contact:{extract_client_ip(request)}", max_requests=12, window_seconds=60)
    row = db.execute(
        text(
            """
            INSERT INTO public_contact_messages (name, email, company, topic, message)
            VALUES (:nm, :em, :co, :tp, :msg)
            RETURNING id::text, created_at
            """
        ),
        {
            "nm": payload.name.strip(),
            "em": payload.email.strip().lower(),
            "co": payload.company.strip(),
            "tp": payload.topic.strip(),
            "msg": payload.message.strip(),
        },
    ).mappings().first()
    db.commit()
    return {"id": row["id"], "status": "received", "created_at": row["created_at"]}
