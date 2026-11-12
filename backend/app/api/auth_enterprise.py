from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.database import get_unscoped_db
from app.core.deps import (
    AuthContext,
    extract_client_ip,
    get_auth_session,
    get_current_context,
    get_session_token_from_request,
    verify_csrf,
)
from app.core.rate_limit import (
    check_api_rate_limit,
    check_login_rate_limit,
    record_failed_login,
    reset_login_rate_limit,
)
from app.core.security import (
    DUMMY_HASH,
    generate_csrf_token,
    generate_mfa_secret,
    generate_random_token,
    get_totp_uri,
    hash_password,
    hash_token,
    slugify_tenant,
    validate_password_strength,
    verify_password,
    verify_totp_code,
)
from app.services.audit import record_audit_log
from app.services.integrations import DEFAULT_INTEGRATIONS
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])

GENERIC_AUTH_ERROR = "Invalid credentials or account temporarily locked."


class RegisterRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    full_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=4, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)
    totp_code: Optional[str] = Field(default=None, max_length=10)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=4, max_length=255)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=200)
    new_password: str = Field(..., min_length=10, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=200)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=10, max_length=128)


class SwitchWorkspaceRequest(BaseModel):
    tenant_id: str = Field(..., min_length=32, max_length=64)


class MfaConfirmRequest(BaseModel):
    secret: str = Field(..., min_length=16, max_length=64)
    totp_code: str = Field(..., min_length=6, max_length=6)


def _set_session_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key="nexora_session",
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,
        path="/",
    )


def _serialize_user_ctx(ctx: AuthContext, db: Session) -> dict:
    memberships = db.execute(
        text("SELECT tenant_id::text, tenant_name, tenant_slug, role_code, is_sample FROM auth_list_user_memberships(:uid)"),
        {"uid": ctx.user_id},
    ).mappings().all()
    return {
        "id": ctx.user_id,
        "email": ctx.email,
        "full_name": ctx.full_name,
        "role_code": ctx.role_code,
        "permissions": sorted(ctx.permissions),
        "is_email_verified": ctx.is_email_verified,
        "mfa_enabled": ctx.mfa_enabled,
        "tenant": {
            "id": ctx.tenant_id,
            "name": ctx.tenant_name,
            "slug": ctx.tenant_slug,
            "currency": ctx.tenant_currency,
            "is_sample": ctx.tenant_is_sample,
        },
        "workspaces": [dict(m) for m in memberships],
        "csrf_token": ctx.csrf_token,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_workspace(
    req: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_unscoped_db),
):
    ip = extract_client_ip(request)
    check_api_rate_limit(f"register:{ip}", max_requests=10, window_seconds=60)

    pw_err = validate_password_strength(req.password)
    if pw_err:
        raise HTTPException(status_code=400, detail=pw_err)

    raw_session = generate_random_token(48)
    csrf = generate_csrf_token()
    raw_verify = generate_random_token(32)
    hashed_pw = hash_password(req.password)

    try:
        res = db.execute(
            text(
                "SELECT * FROM auth_register_workspace(:co, :slug, :em, :fn, :hpw, :sth, :csrf, :vth, :ip, :ua)"
            ),
            {
                "co": req.company_name.strip(),
                "slug": slugify_tenant(req.company_name),
                "em": req.email.strip().lower(),
                "fn": req.full_name.strip(),
                "hpw": hashed_pw,
                "sth": hash_token(raw_session),
                "csrf": csrf,
                "vth": hash_token(raw_verify),
                "ip": ip,
                "ua": request.headers.get("user-agent", ""),
            },
        ).mappings().first()

        # Seed default modular integration catalog inside new tenant RLS context
        tid = str(res["tenant_id"])
        db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": tid})
        for integ in DEFAULT_INTEGRATIONS:
            db.execute(
                text(
                    """
                    INSERT INTO integrations (tenant_id, provider_key, category, name, status)
                    VALUES (:tid, :pk, :cat, :nm, 'not_configured')
                    ON CONFLICT (tenant_id, provider_key) DO NOTHING
                    """
                ),
                {"tid": tid, "pk": integ["provider_key"], "cat": integ["category"], "nm": integ["name"]},
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to register workspace with that email.",
        )

    _set_session_cookie(response, raw_session)
    # Lookup fresh session view
    srow = db.execute(
        text("SELECT * FROM auth_lookup_session(:th)"),
        {"th": hash_token(raw_session)},
    ).mappings().first()
    perm_rows = db.execute(
        text("SELECT p.code FROM roles r JOIN role_permissions rp ON rp.role_id = r.id JOIN permissions p ON p.id = rp.permission_id WHERE r.code = 'owner'")
    ).scalars().all()

    ctx = AuthContext(
        session_id=str(srow["session_id"]),
        tenant_id=str(srow["tenant_id"]),
        tenant_name=srow["tenant_name"],
        tenant_slug=srow["tenant_slug"],
        tenant_currency=srow["tenant_currency"],
        tenant_is_sample=bool(srow["tenant_is_sample"]),
        user_id=str(srow["user_id"]),
        email=srow["email"],
        full_name=srow["full_name"],
        is_email_verified=bool(srow["is_email_verified"]),
        mfa_enabled=bool(srow["mfa_enabled"]),
        role_code=srow["role_code"],
        csrf_token=csrf,
        permissions=set(perm_rows),
        ip_address=ip,
    )
    user_payload = _serialize_user_ctx(ctx, db)
    resp_body = {"user": user_payload, "csrf_token": csrf}
    if settings.APP_ENV == "development":
        resp_body["verification_token"] = raw_verify
    return resp_body


@router.post("/login")
def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_unscoped_db),
):
    ip = extract_client_ip(request)
    email_clean = req.email.strip().lower()
    ip_key = f"ip:{ip}"
    email_key = f"email:{email_clean}"

    ip_ok, _ = check_login_rate_limit(db, ip_key)
    em_ok, _ = check_login_rate_limit(db, email_key)
    if not ip_ok or not em_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    user_row = db.execute(
        text("SELECT * FROM lookup_user_by_email_sec(:em)"),
        {"em": email_clean},
    ).mappings().first()

    if not user_row:
        verify_password(req.password, DUMMY_HASH)
        record_failed_login(db, ip_key)
        record_failed_login(db, email_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    now = datetime.now(timezone.utc)
    if not user_row["is_active"] or (user_row["locked_until"] and user_row["locked_until"] > now):
        record_failed_login(db, ip_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    if not verify_password(req.password, user_row["hashed_password"]):
        db.execute(text("SELECT auth_record_user_login_failure(:uid, 15)"), {"uid": str(user_row["user_id"])})
        db.commit()
        record_failed_login(db, ip_key)
        record_failed_login(db, email_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    if user_row["mfa_enabled"]:
        if not req.totp_code:
            return {"mfa_required": True, "user": None, "csrf_token": ""}
        if not verify_totp_code(user_row["mfa_secret"], req.totp_code):
            record_failed_login(db, email_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authenticator code.")

    memberships = db.execute(
        text("SELECT tenant_id::text, tenant_name, tenant_slug, role_code, is_sample FROM auth_list_user_memberships(:uid)"),
        {"uid": str(user_row["user_id"])},
    ).mappings().all()
    if not memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active workspace membership found.")

    active_m = memberships[0]
    raw_session = generate_random_token(48)
    csrf = generate_csrf_token()
    session_hash = hash_token(raw_session)

    db.execute(
        text("SELECT auth_create_session(:tid, :uid, :sth, :csrf, :ip, :ua)"),
        {
            "tid": active_m["tenant_id"],
            "uid": str(user_row["user_id"]),
            "sth": session_hash,
            "csrf": csrf,
            "ip": ip,
            "ua": request.headers.get("user-agent", ""),
        },
    )
    db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": active_m["tenant_id"]})
    record_audit_log(
        db=db,
        tenant_id=active_m["tenant_id"],
        actor_user_id=str(user_row["user_id"]),
        action="user_logged_in",
        entity_type="session",
        entity_id=str(user_row["user_id"]),
        after={"role_code": active_m["role_code"]},
        ip_address=ip,
        auto_commit=False,
    )
    db.commit()
    reset_login_rate_limit(db, ip_key)
    reset_login_rate_limit(db, email_key)

    _set_session_cookie(response, raw_session)
    srow = db.execute(text("SELECT * FROM auth_lookup_session(:th)"), {"th": session_hash}).mappings().first()
    perm_rows = db.execute(
        text("SELECT p.code FROM roles r JOIN role_permissions rp ON rp.role_id = r.id JOIN permissions p ON p.id = rp.permission_id WHERE r.code = :rc"),
        {"rc": srow["role_code"]},
    ).scalars().all()
    ctx = AuthContext(
        session_id=str(srow["session_id"]),
        tenant_id=str(srow["tenant_id"]),
        tenant_name=srow["tenant_name"],
        tenant_slug=srow["tenant_slug"],
        tenant_currency=srow["tenant_currency"],
        tenant_is_sample=bool(srow["tenant_is_sample"]),
        user_id=str(srow["user_id"]),
        email=srow["email"],
        full_name=srow["full_name"],
        is_email_verified=bool(srow["is_email_verified"]),
        mfa_enabled=bool(srow["mfa_enabled"]),
        role_code=srow["role_code"],
        csrf_token=csrf,
        permissions=set(perm_rows),
        ip_address=ip,
    )
    return {"mfa_required": False, "csrf_token": csrf, "user": _serialize_user_ctx(ctx, db)}


@router.get("/me")
def get_me(auth_and_db=Depends(get_auth_session)):
    ctx, db = auth_and_db
    return _serialize_user_ctx(ctx, db)


@router.post("/logout")
def logout(
    response: Response,
    token: Optional[str] = Depends(get_session_token_from_request),
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    if token:
        db.execute(text("SELECT auth_revoke_session_by_hash(:th)"), {"th": hash_token(token)})
        record_audit_log(db, ctx.tenant_id, ctx.user_id, "user_logged_out", "session", ctx.session_id, ip_address=ctx.ip_address)
    response.delete_cookie("nexora_session", path="/")
    return {"status": "logged_out"}


@router.post("/switch-workspace")
def switch_workspace(
    req: SwitchWorkspaceRequest,
    request: Request,
    response: Response,
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    memberships = db.execute(
        text("SELECT tenant_id::text FROM auth_list_user_memberships(:uid)"),
        {"uid": ctx.user_id},
    ).scalars().all()
    if req.tenant_id not in memberships:
        raise HTTPException(status_code=403, detail="You do not belong to the requested workspace.")

    raw_session = generate_random_token(48)
    csrf = generate_csrf_token()
    session_hash = hash_token(raw_session)
    db.execute(
        text("SELECT auth_create_session(:tid, :uid, :sth, :csrf, :ip, :ua)"),
        {
            "tid": req.tenant_id,
            "uid": ctx.user_id,
            "sth": session_hash,
            "csrf": csrf,
            "ip": ctx.ip_address,
            "ua": request.headers.get("user-agent", ""),
        },
    )
    db.commit()
    _set_session_cookie(response, raw_session)
    return {"status": "switched", "tenant_id": req.tenant_id, "csrf_token": csrf}


@router.post("/forgot-password")
def forgot_password(
    req: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_unscoped_db),
):
    ip = extract_client_ip(request)
    check_api_rate_limit(f"forgot_pw:{ip}", max_requests=8, window_seconds=300)
    raw_token = generate_random_token(32)
    uid = db.execute(
        text("SELECT auth_issue_reset_token(:em, :th)"),
        {"em": req.email.strip().lower(), "th": hash_token(raw_token)},
    ).scalar()
    db.commit()
    resp = {"status": "if_exists_issued"}
    if uid and settings.APP_ENV == "development":
        resp["dev_reset_token"] = raw_token
    return resp


@router.post("/reset-password")
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_unscoped_db),
):
    pw_err = validate_password_strength(req.new_password)
    if pw_err:
        raise HTTPException(status_code=400, detail=pw_err)
    try:
        db.execute(
            text("SELECT auth_consume_reset_token(:th, :hpw)"),
            {"th": hash_token(req.token.strip()), "hpw": hash_password(req.new_password)},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired.")
    return {"status": "password_reset"}


@router.post("/verify-email")
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_unscoped_db)):
    try:
        db.execute(
            text("SELECT auth_consume_email_verify_token(:th)"),
            {"th": hash_token(req.token.strip())},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Verification token is invalid or expired.")
    return {"status": "verified"}


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    pw_err = validate_password_strength(req.new_password)
    if pw_err:
        raise HTTPException(status_code=400, detail=pw_err)
    user_row = db.execute(
        text("SELECT * FROM lookup_user_by_email_sec(:em)"),
        {"em": ctx.email},
    ).mappings().first()
    if not user_row or not verify_password(req.current_password, user_row["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    db.execute(
        text("SELECT auth_change_user_password(:uid, :hpw, :keep_sid)"),
        {"uid": ctx.user_id, "hpw": hash_password(req.new_password), "keep_sid": ctx.session_id},
    )
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "password_changed", "user", ctx.user_id, ip_address=ctx.ip_address)
    return {"status": "updated"}


@router.post("/mfa/setup")
def mfa_setup(_csrf: None = Depends(verify_csrf), ctx: AuthContext = Depends(get_current_context)):
    secret = generate_mfa_secret()
    uri = get_totp_uri(secret, ctx.email)
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/mfa/confirm")
def mfa_confirm(
    req: MfaConfirmRequest,
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    if not verify_totp_code(req.secret, req.totp_code):
        raise HTTPException(status_code=400, detail="Invalid 6-digit verification code for secret.")
    db.execute(
        text("SELECT auth_configure_mfa(:uid, TRUE, :sec)"),
        {"uid": ctx.user_id, "sec": req.secret.strip().upper()},
    )
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "mfa_enabled", "user", ctx.user_id, ip_address=ctx.ip_address)
    return {"mfa_enabled": True}


@router.post("/mfa/disable")
def mfa_disable(
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    db.execute(text("SELECT auth_configure_mfa(:uid, FALSE, NULL)"), {"uid": ctx.user_id})
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "mfa_disabled", "user", ctx.user_id, ip_address=ctx.ip_address)
    return {"mfa_enabled": False}


@router.get("/sessions")
def list_sessions(auth_and_db=Depends(get_auth_session)):
    ctx, db = auth_and_db
    rows = db.execute(
        text(
            """
            SELECT id::text, ip_address, user_agent, expires_at, created_at, (id::text = :sid) AS is_current
            FROM sessions
            WHERE tenant_id = :tid AND user_id = :uid AND revoked_at IS NULL AND expires_at > NOW()
            ORDER BY created_at DESC
            """
        ),
        {"tid": ctx.tenant_id, "uid": ctx.user_id, "sid": ctx.session_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    _csrf: None = Depends(verify_csrf),
    auth_and_db=Depends(get_auth_session),
):
    ctx, db = auth_and_db
    updated = db.execute(
        text(
            """
            UPDATE sessions SET revoked_at = NOW()
            WHERE id = :target AND tenant_id = :tid AND user_id = :uid AND revoked_at IS NULL
            RETURNING id::text
            """
        ),
        {"target": session_id, "tid": ctx.tenant_id, "uid": ctx.user_id},
    ).first()
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found.")
    record_audit_log(db, ctx.tenant_id, ctx.user_id, "session_revoked", "session", session_id, ip_address=ctx.ip_address)
    return {"status": "revoked"}
