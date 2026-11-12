# ADR 0001: Authentication Approach & RLS Bootstrap

## Status
Accepted

## Context
NEXORA Order Agent enforces strict multi-tenancy via PostgreSQL Row-Level Security (RLS) on all tenant-owned tables (`FORCE ROW LEVEL SECURITY`). However, when a user attempts to log in using their email and password, their `tenant_id` is not yet known. Under strict RLS, querying `SELECT * FROM users WHERE email = ...` returns 0 rows because `app.current_tenant_id` is unset.

Furthermore, passwords must be securely hashed against brute-force and GPU-accelerated dictionary attacks.

## Decision
1. **Password Hashing:** Use **Argon2id** (RFC 9106) with memory cost 64 MB ($m=65536$), time cost 3 iterations ($t=3$), and parallelism 4 ($p=4$).
2. **Auth Definer Bootstrap:** Create a dedicated PostgreSQL role `auth_definer` with `NOLOGIN`. Define a `SECURITY DEFINER` function `lookup_user_for_auth(p_email TEXT)` owned by `auth_definer`.
   - `users` has a permissive policy `auth_definer_user_lookup_policy` granting `auth_definer` select on all rows.
   - `lookup_user_for_auth` checks case-insensitive email using `lower(u.email)` backed by a unique index `CREATE UNIQUE INDEX idx_users_lower_email ON users (lower(email))`.
   - The function returns `(user_id, tenant_id, hashed_password, role, name, is_active)`.
3. **Session & RLS Context:** Upon successful Argon2id verification, the backend issues an HTTP-only SameSite=Strict session cookie / Bearer JWT containing `sub` (user_id), `tenant_id`, and `role`.
4. **CSRF Protection:** Double-submit CSRF cookie/header pattern validated on all non-idempotent endpoints (`POST`, `PATCH`, `DELETE`).
5. **Connection RLS Binding:** Every API request sets `SET LOCAL app.current_tenant_id = '<tenant_uuid>'` at the start of the transaction.

## Consequences
- Clean separation of authentication from tenant RLS isolation.
- `api_role` cannot query other tenants' users directly; login lookup is restricted to the specific RPC function.
- Password hashes resist state-of-the-art ASIC cracking.
