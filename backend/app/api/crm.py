import csv
import io
from typing import Optional

from app.core.deps import AuthContext, get_auth_session, require_permission, verify_csrf
from app.services.audit import record_audit_log
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text

router = APIRouter(prefix="/crm", tags=["CRM"])


class CustomerIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    category: str = Field(default="wholesale", max_length=64)
    email: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=64)
    gstin: str = Field(default="", max_length=32)
    billing_address: str = Field(default="", max_length=1000)
    status: str = Field(default="active")
    language_hints: str = Field(default="en,hi", max_length=64)


class ContactIn(BaseModel):
    customer_id: str
    full_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=64)
    designation: str = Field(default="", max_length=120)
    is_primary: bool = False


class LeadIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)
    contact_name: str = Field(default="", max_length=255)
    email: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=64)
    source: str = Field(default="direct", max_length=80)
    stage: str = Field(default="new")
    estimated_value: float = Field(default=0.0, ge=0)
    next_follow_up_at: Optional[str] = None


class ActivityIn(BaseModel):
    entity_type: str = Field(..., pattern="^(customer|lead|order|task)$")
    entity_id: str
    activity_type: str = Field(default="note", pattern="^(note|call|email|meeting|follow_up|system)$")
    summary: str = Field(..., min_length=2, max_length=2000)
    due_at: Optional[str] = None


class AliasIn(BaseModel):
    customer_id: str
    product_id: str
    phrase: str = Field(..., min_length=1, max_length=255)


class CsvImportIn(BaseModel):
    csv_text: str = Field(..., min_length=5, max_length=500000)


def _safe_csv_cell(val: object) -> str:
    s = "" if val is None else str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


@router.get("/customers")
def list_customers(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT c.id::text, c.name, c.category, c.email, c.phone, c.gstin, c.billing_address,
                   c.status, c.language_hints, c.owner_user_id::text, u.full_name AS owner_name,
                   c.created_at, c.updated_at,
                   COUNT(DISTINCT o.id) AS order_count,
                   COALESCE(SUM(o.total_amount) FILTER (WHERE o.status <> 'cancelled'), 0) AS total_spent
            FROM customers c
            LEFT JOIN users u ON u.id = c.owner_user_id
            LEFT JOIN orders o ON o.customer_id = c.id AND o.tenant_id = c.tenant_id
            WHERE c.tenant_id = :tid
              AND (:cat IS NULL OR c.category = :cat)
              AND (:st IS NULL OR c.status = :st)
              AND (:q IS NULL OR c.name ILIKE :q OR c.phone ILIKE :q OR c.email ILIKE :q)
            GROUP BY c.id, u.full_name
            ORDER BY c.name ASC
            """
        ),
        {
            "tid": ctx.tenant_id,
            "cat": category or None,
            "st": status_filter or None,
            "q": f"%{q.strip()}%" if q else None,
        },
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(
    req: CustomerIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO customers (tenant_id, name, category, email, phone, gstin, billing_address, owner_user_id, status, language_hints)
            VALUES (:tid, :nm, :cat, :em, :ph, :gst, :addr, :uid, :st, :lh)
            RETURNING id::text, name, category, email, phone, gstin, billing_address, status, language_hints, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "nm": req.name.strip(),
            "cat": req.category.strip(),
            "em": req.email.strip(),
            "ph": req.phone.strip(),
            "gst": req.gstin.strip().upper(),
            "addr": req.billing_address.strip(),
            "uid": ctx.user_id,
            "st": req.status,
            "lh": req.language_hints.strip(),
        },
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "customer_created", "customer", row["id"], after={"name": row["name"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.get("/customers/{customer_id}")
def get_customer_detail(
    customer_id: str,
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    cust = db.execute(
        text(
            """
            SELECT id::text, name, category, email, phone, gstin, billing_address, status, language_hints, owner_user_id::text, created_at, updated_at
            FROM customers WHERE tenant_id = :tid AND id = :cid
            """
        ),
        {"tid": ctx.tenant_id, "cid": customer_id},
    ).mappings().first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found.")

    contacts = db.execute(
        text("SELECT id::text, full_name, email, phone, designation, is_primary FROM contacts WHERE tenant_id = :tid AND customer_id = :cid ORDER BY is_primary DESC, full_name ASC"),
        {"tid": ctx.tenant_id, "cid": customer_id},
    ).mappings().all()
    activities = db.execute(
        text(
            """
            SELECT a.id::text, a.activity_type, a.summary, a.due_at, a.completed_at, a.created_at, u.full_name AS author_name
            FROM activities a LEFT JOIN users u ON u.id = a.created_by
            WHERE a.tenant_id = :tid AND a.entity_type = 'customer' AND a.entity_id = :cid
            ORDER BY a.created_at DESC LIMIT 50
            """
        ),
        {"tid": ctx.tenant_id, "cid": customer_id},
    ).mappings().all()
    aliases = db.execute(
        text(
            """
            SELECT ca.id::text, ca.phrase, ca.product_id::text, p.name AS product_name, p.sku
            FROM customer_aliases ca JOIN products p ON p.id = ca.product_id
            WHERE ca.tenant_id = :tid AND ca.customer_id = :cid
            ORDER BY ca.phrase ASC
            """
        ),
        {"tid": ctx.tenant_id, "cid": customer_id},
    ).mappings().all()
    orders = db.execute(
        text(
            "SELECT id::text, order_number, status, total_amount, created_at FROM orders WHERE tenant_id = :tid AND customer_id = :cid ORDER BY created_at DESC LIMIT 20"
        ),
        {"tid": ctx.tenant_id, "cid": customer_id},
    ).mappings().all()

    return {
        "customer": dict(cust),
        "contacts": [dict(r) for r in contacts],
        "activities": [dict(r) for r in activities],
        "aliases": [dict(r) for r in aliases],
        "orders": [dict(r) for r in orders],
    }


@router.patch("/customers/{customer_id}")
def update_customer(
    customer_id: str,
    req: CustomerIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            UPDATE customers
            SET name = :nm, category = :cat, email = :em, phone = :ph, gstin = :gst,
                billing_address = :addr, status = :st, language_hints = :lh, updated_at = NOW()
            WHERE tenant_id = :tid AND id = :cid
            RETURNING id::text, name, category, email, phone, gstin, billing_address, status, language_hints, updated_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "cid": customer_id,
            "nm": req.name.strip(),
            "cat": req.category.strip(),
            "em": req.email.strip(),
            "ph": req.phone.strip(),
            "gst": req.gstin.strip().upper(),
            "addr": req.billing_address.strip(),
            "st": req.status,
            "lh": req.language_hints.strip(),
        },
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "customer_updated", "customer", customer_id, after={"name": row["name"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:delete")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    orders_cnt = db.execute(
        text("SELECT COUNT(*) FROM orders WHERE tenant_id = :tid AND customer_id = :cid"),
        {"tid": ctx.tenant_id, "cid": customer_id},
    ).scalar()
    if orders_cnt and orders_cnt > 0:
        raise HTTPException(status_code=409, detail="Customer has existing orders; archive by setting status='inactive' instead.")
    deleted = db.execute(
        text("DELETE FROM customers WHERE tenant_id = :tid AND id = :cid RETURNING id::text"),
        {"tid": ctx.tenant_id, "cid": customer_id},
    ).first()
    if not deleted:
        raise HTTPException(status_code=404, detail="Customer not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "customer_deleted", "customer", customer_id, ip_address=ctx.ip_address)
    return {"status": "deleted"}


@router.get("/customers/export/csv")
def export_customers_csv(
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text("SELECT name, category, email, phone, gstin, billing_address, status FROM customers WHERE tenant_id = :tid ORDER BY name ASC"),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name", "category", "email", "phone", "gstin", "billing_address", "status"])
    for r in rows:
        writer.writerow([
            _safe_csv_cell(r["name"]),
            _safe_csv_cell(r["category"]),
            _safe_csv_cell(r["email"]),
            _safe_csv_cell(r["phone"]),
            _safe_csv_cell(r["gstin"]),
            _safe_csv_cell(r["billing_address"]),
            _safe_csv_cell(r["status"]),
        ])
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "customers_exported_csv", "customer", "batch", ip_address=ctx.ip_address)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="nexora_customers.csv"'},
    )


@router.post("/customers/import/csv")
def import_customers_csv(
    req: CsvImportIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    reader = csv.DictReader(io.StringIO(req.csv_text))
    imported = 0
    for row in reader:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        db.execute(
            text(
                """
                INSERT INTO customers (tenant_id, name, category, email, phone, gstin, billing_address, owner_user_id, status)
                VALUES (:tid, :nm, :cat, :em, :ph, :gst, :addr, :uid, 'active')
                """
            ),
            {
                "tid": ctx.tenant_id,
                "nm": name[:255],
                "cat": (row.get("category") or "wholesale")[:64],
                "em": (row.get("email") or "")[:255],
                "ph": (row.get("phone") or "")[:64],
                "gst": (row.get("gstin") or "")[:32],
                "addr": (row.get("billing_address") or "")[:1000],
                "uid": ctx.user_id,
            },
        )
        imported += 1
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "customers_imported_csv", "customer", "batch", after={"count": imported}, ip_address=ctx.ip_address)
    return {"imported_count": imported}


@router.get("/contacts")
def list_contacts(
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT ct.id::text, ct.customer_id::text, c.name AS customer_name, ct.full_name, ct.email, ct.phone, ct.designation, ct.is_primary
            FROM contacts ct JOIN customers c ON c.id = ct.customer_id
            WHERE ct.tenant_id = :tid ORDER BY ct.full_name ASC
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
def create_contact(
    req: ContactIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO contacts (tenant_id, customer_id, full_name, email, phone, designation, is_primary)
            VALUES (:tid, :cid, :fn, :em, :ph, :ds, :ip)
            RETURNING id::text, customer_id::text, full_name, email, phone, designation, is_primary
            """
        ),
        {"tid": ctx.tenant_id, "cid": req.customer_id, "fn": req.full_name.strip(), "em": req.email.strip(), "ph": req.phone.strip(), "ds": req.designation.strip(), "ip": req.is_primary},
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "contact_created", "contact", row["id"], after={"full_name": row["full_name"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.get("/leads")
def list_leads(
    stage: Optional[str] = Query(default=None),
    _perm: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT l.id::text, l.title, l.company_name, l.contact_name, l.email, l.phone, l.source,
                   l.stage, l.estimated_value, l.customer_id::text, l.next_follow_up_at, l.created_at,
                   u.full_name AS owner_name
            FROM leads l LEFT JOIN users u ON u.id = l.owner_user_id
            WHERE l.tenant_id = :tid AND (:st IS NULL OR l.stage = :st)
            ORDER BY l.created_at DESC
            """
        ),
        {"tid": ctx.tenant_id, "st": stage or None},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/leads", status_code=status.HTTP_201_CREATED)
def create_lead(
    req: LeadIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO leads (tenant_id, title, company_name, contact_name, email, phone, source, stage, estimated_value, owner_user_id, next_follow_up_at)
            VALUES (:tid, :ti, :cn, :con, :em, :ph, :src, :stg, :val, :uid, :nf)
            RETURNING id::text, title, company_name, contact_name, email, phone, source, stage, estimated_value, next_follow_up_at, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "ti": req.title.strip(),
            "cn": req.company_name.strip(),
            "con": req.contact_name.strip(),
            "em": req.email.strip(),
            "ph": req.phone.strip(),
            "src": req.source.strip(),
            "stg": req.stage,
            "val": req.estimated_value,
            "uid": ctx.user_id,
            "nf": req.next_follow_up_at or None,
        },
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "lead_created", "lead", row["id"], after={"title": row["title"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.patch("/leads/{lead_id}")
def update_lead(
    lead_id: str,
    req: LeadIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            UPDATE leads
            SET title = :ti, company_name = :cn, contact_name = :con, email = :em, phone = :ph,
                source = :src, stage = :stg, estimated_value = :val, next_follow_up_at = :nf, updated_at = NOW()
            WHERE tenant_id = :tid AND id = :lid
            RETURNING id::text, title, company_name, contact_name, email, phone, source, stage, estimated_value, next_follow_up_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "lid": lead_id,
            "ti": req.title.strip(),
            "cn": req.company_name.strip(),
            "con": req.contact_name.strip(),
            "em": req.email.strip(),
            "ph": req.phone.strip(),
            "src": req.source.strip(),
            "stg": req.stage,
            "val": req.estimated_value,
            "nf": req.next_follow_up_at or None,
        },
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "lead_updated", "lead", lead_id, after={"stage": row["stage"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.post("/leads/{lead_id}/convert")
def convert_lead_to_customer(
    lead_id: str,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    lead = db.execute(
        text("SELECT * FROM leads WHERE tenant_id = :tid AND id = :lid"),
        {"tid": ctx.tenant_id, "lid": lead_id},
    ).mappings().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    cust = db.execute(
        text(
            """
            INSERT INTO customers (tenant_id, name, category, email, phone, owner_user_id, status)
            VALUES (:tid, :nm, 'wholesale', :em, :ph, :uid, 'active')
            RETURNING id::text, name
            """
        ),
        {"tid": ctx.tenant_id, "nm": lead["company_name"], "em": lead["email"] or "", "ph": lead["phone"] or "", "uid": ctx.user_id},
    ).mappings().first()
    if lead["contact_name"]:
        db.execute(
            text("INSERT INTO contacts (tenant_id, customer_id, full_name, email, phone, is_primary) VALUES (:tid, :cid, :fn, :em, :ph, TRUE)"),
            {"tid": ctx.tenant_id, "cid": cust["id"], "fn": lead["contact_name"], "em": lead["email"] or "", "ph": lead["phone"] or ""},
        )
    db.execute(
        text("UPDATE leads SET stage = 'won', customer_id = :cid, updated_at = NOW() WHERE tenant_id = :tid AND id = :lid"),
        {"cid": cust["id"], "tid": ctx.tenant_id, "lid": lead_id},
    )
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "lead_converted", "lead", lead_id, after={"customer_id": cust["id"]}, ip_address=ctx.ip_address)
    return {"lead_id": lead_id, "customer_id": cust["id"], "customer_name": cust["name"]}


@router.post("/activities", status_code=status.HTTP_201_CREATED)
def log_activity(
    req: ActivityIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO activities (tenant_id, entity_type, entity_id, activity_type, summary, due_at, created_by)
            VALUES (:tid, :et, :eid, :at, :sm, :du, :uid)
            RETURNING id::text, entity_type, entity_id::text, activity_type, summary, due_at, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "et": req.entity_type,
            "eid": req.entity_id,
            "at": req.activity_type,
            "sm": req.summary.strip(),
            "du": req.due_at or None,
            "uid": ctx.user_id,
        },
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "activity_logged", req.entity_type, req.entity_id, after={"summary": row["summary"]}, ip_address=ctx.ip_address)
    return dict(row)


@router.post("/aliases", status_code=status.HTTP_201_CREATED)
def add_customer_alias(
    req: AliasIn,
    _csrf: None = Depends(verify_csrf),
    _perm: AuthContext = Depends(require_permission("crm:write")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    row = db.execute(
        text(
            """
            INSERT INTO customer_aliases (tenant_id, customer_id, product_id, phrase, source)
            VALUES (:tid, :cid, :pid, :ph, 'manual')
            ON CONFLICT (tenant_id, customer_id, phrase) DO UPDATE SET product_id = EXCLUDED.product_id
            RETURNING id::text, customer_id::text, product_id::text, phrase
            """
        ),
        {"tid": ctx.tenant_id, "cid": req.customer_id, "pid": req.product_id, "ph": req.phrase.strip().lower()},
    ).mappings().first()
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "alias_saved", "customer_alias", row["id"], after={"phrase": row["phrase"]}, ip_address=ctx.ip_address)
    return dict(row)
