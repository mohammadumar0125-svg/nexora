from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.database import get_unscoped_db
from app.core.deps import (
    AuthContext,
    extract_client_ip,
    get_auth_session,
    require_permission,
    verify_csrf,
)
from app.core.security import (
    generate_random_token,
    hash_password,
    hash_token,
    validate_password_strength,
)
from app.services.audit import record_audit_log
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(tags=["Team & Invitations"])

VALID_ROLES = {"owner", "admin", "manager", "staff", "viewer"}


class InviteRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    role_code: str = Field(..., min_length=3, max_length=40)


class MembershipUpdateRequest(BaseModel):
    role_code: Optional[str] = None
    status: Optional[str] = None


class AcceptInviteRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=200)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=10, max_length=128)


@router.get("/team")
def list_team(
    _ctx: AuthContext = Depends(require_permission("crm:read")),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    members = db.execute(
        text(
            """
            SELECT m.id::text AS membership_id, m.user_id::text, u.email, u.full_name, u.is_email_verified,
                   u.mfa_enabled, m.role_code, m.status, u.last_login_at, m.created_at
            FROM memberships m
            JOIN users u ON u.id = m.user_id
            WHERE m.tenant_id = :tid
            ORDER BY m.created_at ASC
            """
        ),
        {"tid": ctx.tenant_id},
    ).mappings().all()

    invites = []
    if "team:manage" in ctx.permissions:
        invites_rows = db.execute(
            text(
                """
                SELECT id::text, email, role_code, status, expires_at, created_at
                FROM invitations
                WHERE tenant_id = :tid
                ORDER BY created_at DESC
                LIMIT 30
                """
            ),
            {"tid": ctx.tenant_id},
        ).mappings().all()
        invites = [dict(r) for r in invites_rows]

    roles_rows = db.execute(
        text(
            """
            SELECT r.code, r.name, r.description,
                   COALESCE(array_agg(p.code ORDER BY p.code) FILTER (WHERE p.code IS NOT NULL), '{}') AS permissions
            FROM roles r
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id
            GROUP BY r.code, r.name, r.description
            ORDER BY r.name ASC
            """
        )
    ).mappings().all()

    return {
        "members": [dict(r) for r in members],
        "invitations": invites,
        "roles": [dict(r) for r in roles_rows],
    }


@router.post("/team/invite", status_code=status.HTTP_201_CREATED)
def invite_member(
    req: InviteRequest,
    _csrf: None = Depends(verify_csrf),
    ctx: AuthContext = Depends(require_permission("team:manage")),
    auth_and_db=Depends(get_auth_session),
):
    _, db = auth_and_db
    role_clean = req.role_code.strip().lower()
    if role_clean not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role specified.")
    if role_clean == "owner" and ctx.role_code != "owner":
        raise HTTPException(status_code=403, detail="Only owners can invite another owner.")

    raw_token = generate_random_token(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    row = db.execute(
        text(
            """
            INSERT INTO invitations (tenant_id, email, role_code, invited_by_user_id, token_hash, status, expires_at)
            VALUES (:tid, :em, :rc, :by, :th, 'pending', :exp)
            RETURNING id::text, email, role_code, status, expires_at, created_at
            """
        ),
        {
            "tid": ctx.tenant_id,
            "em": req.email.strip().lower(),
            "rc": role_clean,
            "by": ctx.user_id,
            "th": hash_token(raw_token),
            "exp": expires_at,
        },
    ).mappings().first()

    record_audit_log(
        db,
        ctx.tenant_id,
        ctx.user_id,
        "member_invited",
        "invitation",
        row["id"],
        after={"email": row["email"], "role_code": row["role_code"]},
        ip_address=ctx.ip_address,
    )
    out = dict(row)
    out["invite_token"] = raw_token
    out["invite_url"] = f"/accept-invite?token={raw_token}"
    return out


@router.patch("/team/memberships/{target_user_id}")
def update_membership(
    target_user_id: str,
    req: MembershipUpdateRequest,
    _csrf: None = Depends(verify_csrf),
    ctx: AuthContext = Depends(require_permission("team:manage")),
    auth_and_db=Depends(get_auth_session),
):
    _, db = auth_and_db
    target = db.execute(
        text("SELECT id::text, role_code, status FROM memberships WHERE tenant_id = :tid AND user_id = :uid"),
        {"tid": ctx.tenant_id, "uid": target_user_id},
    ).mappings().first()
    if not target:
        raise HTTPException(status_code=404, detail="Membership not found in workspace.")

    new_role = (req.role_code or target["role_code"]).lower()
    new_status = (req.status or target["status"]).lower()
    if new_role not in VALID_ROLES or new_status not in ("active", "suspended"):
        raise HTTPException(status_code=400, detail="Invalid role or membership status.")

    # Guard against removing/demoting the last active owner
    if target["role_code"] == "owner" and (new_role != "owner" or new_status != "active"):
        owners_left = db.execute(
            text(
                "SELECT COUNT(*) FROM memberships WHERE tenant_id = :tid AND role_code = 'owner' AND status = 'active'"
            ),
            {"tid": ctx.tenant_id},
        ).scalar()
        if owners_left <= 1:
            raise HTTPException(status_code=400, detail="Workspace must retain at least one active owner.")

    role_id = db.execute(text("SELECT id FROM roles WHERE code = :rc"), {"rc": new_role}).scalar()
    db.execute(
        text(
            "UPDATE memberships SET role_id = :rid, role_code = :rc, status = :st WHERE tenant_id = :tid AND user_id = :uid"
        ),
        {"rid": role_id, "rc": new_role, "st": new_status, "tid": ctx.tenant_id, "uid": target_user_id},
    )
    if new_status == "suspended":
        db.execute(
            text("UPDATE sessions SET revoked_at = NOW() WHERE tenant_id = :tid AND user_id = :uid AND revoked_at IS NULL"),
            {"tid": ctx.tenant_id, "uid": target_user_id},
        )
    record_audit_log(
        db,
        ctx.tenant_id,
        ctx.user_id,
        "membership_updated",
        "membership",
        target_user_id,
        before={"role_code": target["role_code"], "status": target["status"]},
        after={"role_code": new_role, "status": new_status},
        ip_address=ctx.ip_address,
    )
    return {"user_id": target_user_id, "role_code": new_role, "status": new_status}


@router.post("/invitations/accept")
def accept_invitation(
    req: AcceptInviteRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_unscoped_db),
):
    pw_err = validate_password_strength(req.password)
    if pw_err:
        raise HTTPException(status_code=400, detail=pw_err)

    raw_session = generate_random_token(48)
    csrf = generate_random_token(32)
    ip = extract_client_ip(request)
    try:
        res = db.execute(
            text("SELECT * FROM auth_accept_invitation(:th, :fn, :hpw, :sth, :csrf, :ip)"),
            {
                "th": hash_token(req.token.strip()),
                "fn": req.full_name.strip(),
                "hpw": hash_password(req.password),
                "sth": hash_token(raw_session),
                "csrf": csrf,
                "ip": ip,
            },
        ).mappings().first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invitation token is invalid or expired.")

    response.set_cookie(
        key="nexora_session",
        value=raw_session,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,
        path="/",
    )
    return {
        "tenant_id": str(res["tenant_id"]),
        "user_id": str(res["user_id"]),
        "role_code": res["role_code"],
        "csrf_token": csrf,
    }
