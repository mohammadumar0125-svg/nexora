-- ============================================================================
-- NEXORA Enterprise SaaS Platform - Minimal Hardened SECURITY DEFINER Auth RPCs
-- Enables api_role to remain bound by FORCE ROW LEVEL SECURITY everywhere else.
-- ============================================================================

-- 1. Lookup session + membership + user for incoming session cookie
CREATE OR REPLACE FUNCTION auth_lookup_session(p_session_token_hash TEXT)
RETURNS TABLE (
    session_id UUID,
    tenant_id UUID,
    tenant_name VARCHAR(255),
    tenant_slug VARCHAR(120),
    tenant_currency VARCHAR(12),
    tenant_is_sample BOOLEAN,
    user_id UUID,
    email VARCHAR(255),
    full_name VARCHAR(255),
    is_email_verified BOOLEAN,
    mfa_enabled BOOLEAN,
    role_code VARCHAR(40),
    csrf_token VARCHAR(64),
    expires_at TIMESTAMPTZ
)
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT s.id, t.id, t.name, t.slug, t.currency, t.is_sample,
           u.id, u.email, u.full_name, u.is_email_verified, u.mfa_enabled,
           m.role_code, s.csrf_token, s.expires_at
    FROM sessions s
    JOIN users u ON u.id = s.user_id
    JOIN tenants t ON t.id = s.tenant_id
    JOIN memberships m ON m.tenant_id = s.tenant_id AND m.user_id = s.user_id
    WHERE s.session_token_hash = p_session_token_hash
      AND s.revoked_at IS NULL
      AND s.expires_at > NOW()
      AND u.is_active = TRUE
      AND m.status = 'active';
END;
$$;

-- 2. List all active workspace memberships for an authenticated user (workspace switcher)
CREATE OR REPLACE FUNCTION auth_list_user_memberships(p_user_id UUID)
RETURNS TABLE (
    tenant_id UUID,
    tenant_name VARCHAR(255),
    tenant_slug VARCHAR(120),
    role_code VARCHAR(40),
    is_sample BOOLEAN
)
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.name, t.slug, m.role_code, t.is_sample
    FROM memberships m
    JOIN tenants t ON t.id = m.tenant_id
    WHERE m.user_id = p_user_id
      AND m.status = 'active'
    ORDER BY t.created_at ASC;
END;
$$;

-- 3. Register new business tenant + owner user + membership + session atomically
CREATE OR REPLACE FUNCTION auth_register_workspace(
    p_company_name TEXT,
    p_slug TEXT,
    p_email TEXT,
    p_full_name TEXT,
    p_hashed_password TEXT,
    p_session_token_hash TEXT,
    p_csrf_token TEXT,
    p_verify_token_hash TEXT,
    p_ip_address TEXT DEFAULT '',
    p_user_agent TEXT DEFAULT ''
)
RETURNS TABLE (
    tenant_id UUID,
    user_id UUID,
    session_id UUID
)
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    v_tenant_id UUID;
    v_user_id UUID;
    v_role_id UUID;
    v_session_id UUID;
BEGIN
    SELECT id INTO v_role_id FROM roles WHERE code = 'owner' LIMIT 1;
    IF v_role_id IS NULL THEN
        RAISE EXCEPTION 'System role owner is missing';
    END IF;

    INSERT INTO tenants (name, slug, is_sample)
    VALUES (p_company_name, p_slug, FALSE)
    RETURNING id INTO v_tenant_id;

    INSERT INTO users (email, hashed_password, full_name, is_email_verified, is_active)
    VALUES (lower(trim(p_email)), p_hashed_password, trim(p_full_name), FALSE, TRUE)
    RETURNING id INTO v_user_id;

    INSERT INTO memberships (tenant_id, user_id, role_id, role_code, status)
    VALUES (v_tenant_id, v_user_id, v_role_id, 'owner', 'active');

    INSERT INTO sessions (tenant_id, user_id, session_token_hash, csrf_token, ip_address, user_agent, expires_at)
    VALUES (v_tenant_id, v_user_id, p_session_token_hash, p_csrf_token, p_ip_address, left(p_user_agent, 250), NOW() + INTERVAL '8 hours')
    RETURNING id INTO v_session_id;

    INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at)
    VALUES (v_user_id, 'email_verify', p_verify_token_hash, NOW() + INTERVAL '24 hours');

    INSERT INTO audit_logs (tenant_id, actor_user_id, action, entity_type, entity_id, after_json, ip_address)
    VALUES (
        v_tenant_id,
        v_user_id,
        'workspace_registered',
        'tenant',
        v_tenant_id::text,
        jsonb_build_object('company_name', p_company_name, 'email', lower(trim(p_email))),
        p_ip_address
    );

    RETURN QUERY SELECT v_tenant_id, v_user_id, v_session_id;
END;
$$;

-- 4. Create session on login / workspace switch
CREATE OR REPLACE FUNCTION auth_create_session(
    p_tenant_id UUID,
    p_user_id UUID,
    p_session_token_hash TEXT,
    p_csrf_token TEXT,
    p_ip_address TEXT DEFAULT '',
    p_user_agent TEXT DEFAULT ''
)
RETURNS UUID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    v_session_id UUID;
BEGIN
    -- Verify active membership exists
    IF NOT EXISTS (
        SELECT 1 FROM memberships m
        WHERE m.tenant_id = p_tenant_id AND m.user_id = p_user_id AND m.status = 'active'
    ) THEN
        RAISE EXCEPTION 'User does not hold an active membership in this tenant';
    END IF;

    INSERT INTO sessions (tenant_id, user_id, session_token_hash, csrf_token, ip_address, user_agent, expires_at)
    VALUES (p_tenant_id, p_user_id, p_session_token_hash, p_csrf_token, p_ip_address, left(p_user_agent, 250), NOW() + INTERVAL '8 hours')
    RETURNING id INTO v_session_id;

    UPDATE users SET last_login_at = NOW(), failed_login_attempts = 0, locked_until = NULL
    WHERE id = p_user_id;

    RETURN v_session_id;
END;
$$;

-- 5. Revoke session cleanly by token hash
CREATE OR REPLACE FUNCTION auth_revoke_session_by_hash(p_session_token_hash TEXT)
RETURNS VOID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE sessions SET revoked_at = NOW()
    WHERE session_token_hash = p_session_token_hash AND revoked_at IS NULL;
END;
$$;

-- 6. Record failed login attempt on user safely before tenant context exists
CREATE OR REPLACE FUNCTION auth_record_user_login_failure(p_user_id UUID, p_lock_minutes INT DEFAULT 15)
RETURNS INT
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    v_attempts INT;
BEGIN
    UPDATE users
    SET failed_login_attempts = failed_login_attempts + 1,
        locked_until = CASE WHEN failed_login_attempts + 1 >= 5 THEN NOW() + (p_lock_minutes || ' minutes')::interval ELSE locked_until END
    WHERE id = p_user_id
    RETURNING failed_login_attempts INTO v_attempts;
    RETURN COALESCE(v_attempts, 0);
END;
$$;

-- 7. Lookup & accept invitation by token hash
CREATE OR REPLACE FUNCTION auth_accept_invitation(
    p_token_hash TEXT,
    p_full_name TEXT,
    p_hashed_password TEXT,
    p_session_token_hash TEXT,
    p_csrf_token TEXT,
    p_ip_address TEXT DEFAULT ''
)
RETURNS TABLE (
    tenant_id UUID,
    user_id UUID,
    role_code VARCHAR(40),
    session_id UUID
)
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
#variable_conflict use_column
DECLARE
    v_inv invitations%ROWTYPE;
    v_user_id UUID;
    v_role_id UUID;
    v_session_id UUID;
BEGIN
    SELECT * INTO v_inv FROM invitations
    WHERE token_hash = p_token_hash AND status = 'pending' AND expires_at > NOW()
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invitation token is invalid or expired';
    END IF;

    SELECT id INTO v_role_id FROM roles WHERE code = v_inv.role_code LIMIT 1;

    SELECT id INTO v_user_id FROM users WHERE lower(email) = lower(v_inv.email) LIMIT 1;
    IF v_user_id IS NULL THEN
        INSERT INTO users (email, hashed_password, full_name, is_email_verified, is_active)
        VALUES (lower(v_inv.email), p_hashed_password, trim(p_full_name), TRUE, TRUE)
        RETURNING id INTO v_user_id;
    END IF;

    INSERT INTO memberships (tenant_id, user_id, role_id, role_code, status)
    VALUES (v_inv.tenant_id, v_user_id, v_role_id, v_inv.role_code, 'active')
    ON CONFLICT (tenant_id, user_id) DO UPDATE SET role_id = v_role_id, role_code = v_inv.role_code, status = 'active';

    UPDATE invitations SET status = 'accepted', accepted_at = NOW() WHERE id = v_inv.id;

    INSERT INTO sessions (tenant_id, user_id, session_token_hash, csrf_token, ip_address, expires_at)
    VALUES (v_inv.tenant_id, v_user_id, p_session_token_hash, p_csrf_token, p_ip_address, NOW() + INTERVAL '8 hours')
    RETURNING id INTO v_session_id;

    RETURN QUERY SELECT v_inv.tenant_id, v_user_id, v_inv.role_code, v_session_id;
END;
$$;

-- Restrict RPC execution strictly to api_role
REVOKE ALL ON FUNCTION lookup_user_by_email_sec(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION lookup_user_by_email_sec(TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_lookup_session(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_lookup_session(TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_list_user_memberships(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_list_user_memberships(UUID) TO api_role;

REVOKE ALL ON FUNCTION auth_register_workspace(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_register_workspace(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_create_session(UUID, UUID, TEXT, TEXT, TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_create_session(UUID, UUID, TEXT, TEXT, TEXT, TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_revoke_session_by_hash(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_revoke_session_by_hash(TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_record_user_login_failure(UUID, INT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_record_user_login_failure(UUID, INT) TO api_role;

REVOKE ALL ON FUNCTION auth_accept_invitation(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_accept_invitation(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) TO api_role;
