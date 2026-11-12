# NEXORA Security & Privacy Architecture Review

> Notice: No software platform is immune from all risks. This document records the controls actively implemented and tested in NEXORA without claiming external compliance certifications.

## 1. Authentication & Session Controls (`backend/app/api/auth_enterprise.py`, `backend/app/core/security.py`)
- **Password Hashing:** Argon2id (`time_cost=3`, `memory_cost=65536`, `parallelism=4`) with minimum length (10 chars) and uppercase/lowercase/digit/symbol validation.
- **Session Cookies:** Cryptographic tokens hashed via SHA-256 before persistence in `sessions`; raw tokens stored exclusively in `HttpOnly`, `SameSite=Lax` cookies (`Secure` enforced automatically when `APP_ENV` is `staging` or `production`).
- **CSRF Protection:** Per-session CSRF secret checked via constant-time `secrets.compare_digest` on mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`).
- **MFA & Lockout:** Pure-Python RFC 6238 TOTP MFA (`auth/mfa/setup`, `confirm`, `disable`) + PostgreSQL-backed `login_rate_limits` window and automatic account lockouts after 5 consecutive failed logins.
- **Single-Use Tokens & Revocation:** Reset password tokens (`30 min` TTL) revoke all existing sessions on consumption; suspending a member or rotating password invalidates affected active sessions immediately.

## 2. Multi-Tenant Isolation (`backend/db/migrations/002_rls_and_security.sql`)
- All tenant tables carry `tenant_id` and enable `FORCE ROW LEVEL SECURITY` using `current_tenant_uuid()`.
- FastAPI API sessions connect exclusively as least-privilege `api_role` and set transaction-local `app.current_tenant_id` only after verifying an active session and membership. When unset (`''`), `FORCE ROW LEVEL SECURITY` blocks reads and writes fail-closed.
- Auth RPCs run cleanly inside narrow `SECURITY DEFINER` PostgreSQL functions locked with `REVOKE ALL FROM PUBLIC` and explicit `GRANT EXECUTE TO api_role`.

## 3. Transactional Integrity & Concurrency (`backend/db/migrations/004_auth_tokens_and_stock_rpcs.sql`)
- Order approvals execute inside `confirm_order_atomic`, locking inventory rows (`SELECT ... FOR UPDATE`) in deterministic `product_id` order to eliminate deadlocks and block concurrent over-allocation (`Insufficient stock`).

## 4. Audit Immutability, AI Safety & Storage
- **`audit_logs`:** Protected by `trg_audit_logs_immutable` (`BEFORE UPDATE OR DELETE`) rejecting log tampering.
- **AI Safety:** User inputs are sanitized and checked against prompt-injection patterns; queries read strictly from the caller's tenant snapshot, never expose server API keys to browser bundles, and require human confirmation for consequential actions.
- **Uploads (`backend/app/services/storage.py`):** Filenames sanitized (`os.path.basename` + whitelist regex), size capped (`5 MB` default), allowlisted MIME extensions validated against magic-byte headers (`%PDF`, PNG, JPEG).

## 5. India DPDP & Privacy Readiness Practices
- Explicit separation of sample evaluation tenants (`is_sample = TRUE`), tenant retention window settings (`retention_days`), server-only secret storage, and downloadable organization records via tenant-scoped CSV exports.
