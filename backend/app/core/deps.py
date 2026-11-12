from dataclasses import dataclass
from typing import Callable, Iterable, Optional, Set, Tuple

from app.core.database import SessionLocal, apply_rls_tenant
from app.core.security import hash_token, verify_csrf_token
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class AuthContext:
    session_id: str
    tenant_id: str
    tenant_name: str
    tenant_slug: str
    tenant_currency: str
    tenant_is_sample: bool
    user_id: str
    email: str
    full_name: str
    is_email_verified: bool
    mfa_enabled: bool
    role_code: str
    csrf_token: str
    permissions: Set[str]
    ip_address: str = ""


def extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "127.0.0.1")[:64]


def get_session_token_from_request(
    session_cookie: Optional[str] = Cookie(None, alias="nexora_session"),
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    if session_cookie:
        return session_cookie
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def get_auth_session(
    request: Request,
    token: Optional[str] = Depends(get_session_token_from_request),
) -> Tuple[AuthContext, Session]:
    """
    Authenticates the request, loads user permissions, and opens a PostgreSQL
    session strictly bound to app.current_tenant_id (FORCE ROW LEVEL SECURITY).
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    db = SessionLocal()
    try:
        db.execute(text("SET LOCAL app.current_tenant_id = ''"))
        token_hash = hash_token(token)
        row = db.execute(
            text("SELECT * FROM auth_lookup_session(:th)"),
            {"th": token_hash},
        ).mappings().first()

        if not row:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session is invalid or expired.",
            )

        perm_rows = db.execute(
            text(
                """
                SELECT p.code
                FROM roles r
                JOIN role_permissions rp ON rp.role_id = r.id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE r.code = :rc
                """
            ),
            {"rc": row["role_code"]},
        ).scalars().all()

        tenant_id = str(row["tenant_id"])
        apply_rls_tenant(db, tenant_id)

        ctx = AuthContext(
            session_id=str(row["session_id"]),
            tenant_id=tenant_id,
            tenant_name=row["tenant_name"],
            tenant_slug=row["tenant_slug"],
            tenant_currency=row["tenant_currency"],
            tenant_is_sample=bool(row["tenant_is_sample"]),
            user_id=str(row["user_id"]),
            email=row["email"],
            full_name=row["full_name"],
            is_email_verified=bool(row["is_email_verified"]),
            mfa_enabled=bool(row["mfa_enabled"]),
            role_code=row["role_code"],
            csrf_token=row["csrf_token"],
            permissions=set(perm_rows),
            ip_address=extract_client_ip(request),
        )
        yield ctx, db
    finally:
        db.close()


def get_current_context(
    auth_and_db: Tuple[AuthContext, Session] = Depends(get_auth_session),
) -> AuthContext:
    return auth_and_db[0]


def get_tenant_db_session(
    auth_and_db: Tuple[AuthContext, Session] = Depends(get_auth_session),
) -> Session:
    return auth_and_db[1]


def verify_csrf(
    request: Request,
    ctx: AuthContext = Depends(get_current_context),
) -> None:
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        header_token = request.headers.get("X-CSRF-Token") or request.headers.get("x-csrf-token")
        if not verify_csrf_token(header_token, ctx.csrf_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed.",
            )


def require_permission(permission_code: str) -> Callable[[AuthContext], AuthContext]:
    def checker(ctx: AuthContext = Depends(get_current_context)) -> AuthContext:
        if permission_code not in ctx.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_code}' required.",
            )
        return ctx

    return checker


def require_roles(allowed_roles: Iterable[str]) -> Callable[[AuthContext], AuthContext]:
    allowed_set = set(allowed_roles)

    def checker(ctx: AuthContext = Depends(get_current_context)) -> AuthContext:
        if ctx.role_code not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {sorted(allowed_set)}.",
            )
        return ctx

    return checker
