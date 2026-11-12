-- Migration: 002_auth_sessions_and_team.sql
-- Description: User session management, lockout protection, tenant settings, and login rate limiting.

-- ============================================================================
-- 1. ALTER USERS TABLE
-- ============================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INT NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ NULL;

-- ============================================================================
-- 2. USER SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    session_token_hash VARCHAR(64) UNIQUE NOT NULL,
    csrf_token VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_sessions_user FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT uq_user_sessions_tenant_id UNIQUE (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON user_sessions (session_token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions (expires_at);

-- ============================================================================
-- 3. TENANT SETTINGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tenant_settings (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    manual_baseline_seconds NUMERIC(10, 2) NOT NULL DEFAULT 240.0,
    session_timeout_minutes INT NOT NULL DEFAULT 480,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. LOGIN RATE LIMITS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS login_rate_limits (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL, -- e.g. "email:user@domain.com" or "ip:1.2.3.4"
    attempts INT NOT NULL DEFAULT 1,
    first_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    locked_until TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON login_rate_limits (key);

-- ============================================================================
-- 5. UPDATE SECURITY DEFINER AUTH FUNCTION
-- ============================================================================
DROP FUNCTION IF EXISTS lookup_user_for_auth(TEXT);
CREATE OR REPLACE FUNCTION lookup_user_for_auth(p_email TEXT)
RETURNS TABLE (
    user_id UUID,
    tenant_id UUID,
    hashed_password VARCHAR(255),
    role VARCHAR(50),
    name VARCHAR(255),
    is_active BOOLEAN,
    must_change_password BOOLEAN,
    failed_login_attempts INT,
    locked_until TIMESTAMPTZ
)
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.tenant_id, u.hashed_password, u.role, u.name, u.is_active,
           u.must_change_password, u.failed_login_attempts, u.locked_until
    FROM users u
    WHERE lower(u.email) = lower(p_email) AND u.is_active = TRUE;
END;
$$;

ALTER FUNCTION lookup_user_for_auth(TEXT) OWNER TO auth_definer;
REVOKE ALL ON FUNCTION lookup_user_for_auth(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION lookup_user_for_auth(TEXT) TO api_role;

-- ============================================================================
-- 6. RLS FOR NEW TENANT TABLES
-- ============================================================================
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_policy ON user_sessions;
CREATE POLICY tenant_isolation_policy ON user_sessions
    AS PERMISSIVE
    FOR ALL
    TO api_role, worker_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

ALTER TABLE tenant_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_settings FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_policy ON tenant_settings;
CREATE POLICY tenant_isolation_policy ON tenant_settings
    AS PERMISSIVE
    FOR ALL
    TO api_role, worker_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- ============================================================================
-- 7. GRANTS FOR NEW TABLES
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions, tenant_settings, login_rate_limits TO api_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_role;

GRANT SELECT ON tenant_settings TO worker_role;
