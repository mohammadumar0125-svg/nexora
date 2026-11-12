-- ============================================================================
-- NEXORA Enterprise SaaS Platform - RLS Policies, Immutable Audit, Roles & RPCs
-- ============================================================================

-- 1. Ensure least-privilege roles exist and clean privileges
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_role') THEN
        CREATE ROLE api_role WITH LOGIN PASSWORD 'api_secret_pass';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'worker_role') THEN
        CREATE ROLE worker_role WITH LOGIN PASSWORD 'worker_secret_pass';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_definer') THEN
        CREATE ROLE auth_definer WITH NOLOGIN;
    END IF;
END $$;

GRANT USAGE ON SCHEMA public TO api_role, worker_role, auth_definer;

-- 2. Immutable Audit Log Protection
CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs table is append-only; UPDATE and DELETE are forbidden.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_logs_immutable ON audit_logs;
CREATE TRIGGER trg_audit_logs_immutable
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();

-- 3. Security-Definer Authentication Lookup (Runs ONLY inside auth endpoints)
CREATE OR REPLACE FUNCTION lookup_user_by_email_sec(p_email TEXT)
RETURNS TABLE (
    user_id UUID,
    email VARCHAR(255),
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    is_email_verified BOOLEAN,
    is_active BOOLEAN,
    mfa_enabled BOOLEAN,
    mfa_secret VARCHAR(128),
    failed_login_attempts INT,
    locked_until TIMESTAMPTZ
)
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.email, u.hashed_password, u.full_name, u.is_email_verified,
           u.is_active, u.mfa_enabled, u.mfa_secret, u.failed_login_attempts, u.locked_until
    FROM users u
    WHERE lower(u.email) = lower(p_email);
END;
$$;

-- 4. Current Tenant Helper (Fail-closed when unset)
CREATE OR REPLACE FUNCTION current_app_tenant_id()
RETURNS UUID AS $$
    SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::uuid;
$$ LANGUAGE SQL STABLE;

-- 5. Enable & Force Row-Level Security on ALL Tenant-Scoped Tables
DO $$
DECLARE
    tbl TEXT;
    tenant_tables TEXT[] := ARRAY[
        'memberships',
        'invitations',
        'sessions',
        'customers',
        'contacts',
        'leads',
        'activities',
        'notes',
        'suppliers',
        'products',
        'inventory',
        'stock_movements',
        'customer_aliases',
        'tenant_counters',
        'orders',
        'order_items',
        'tasks',
        'notifications',
        'automation_workflows',
        'automation_executions',
        'ai_interactions',
        'audit_logs',
        'integrations',
        'files'
    ];
BEGIN
    FOREACH tbl IN ARRAY tenant_tables LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', tbl);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY;', tbl);
        EXECUTE format('DROP POLICY IF EXISTS nexora_tenant_isolation ON %I;', tbl);
        EXECUTE format(
            'CREATE POLICY nexora_tenant_isolation ON %I AS PERMISSIVE FOR ALL TO api_role USING (tenant_id = current_app_tenant_id()) WITH CHECK (tenant_id = current_app_tenant_id());',
            tbl
        );
    END LOOP;
END $$;

-- Tenants table policy (can see only active tenant context)
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS nexora_tenant_self ON tenants;
CREATE POLICY nexora_tenant_self ON tenants
    AS PERMISSIVE FOR ALL TO api_role
    USING (id = current_app_tenant_id())
    WITH CHECK (id = current_app_tenant_id());

-- Grant operational permissions to api_role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO api_role;
REVOKE UPDATE, DELETE ON audit_logs FROM api_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_role;

-- 6. Seed Standard System Roles & Granular Permissions
INSERT INTO roles (code, name, description) VALUES
    ('owner', 'Workspace Owner', 'Full tenant control including team management, security policies and deletions'),
    ('admin', 'Administrator', 'Manage operations, team members, integrations and security views'),
    ('manager', 'Operations Manager', 'Approve orders, manage inventory, CRM pipelines and workflow automations'),
    ('staff', 'Operations Staff', 'Create customers, leads, draft orders, tasks and log activities'),
    ('viewer', 'Read-Only Viewer', 'View permitted reports and records without mutation permissions')
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (code, description) VALUES
    ('crm:read', 'View customers, contacts, leads and timelines'),
    ('crm:write', 'Create and update CRM records'),
    ('crm:delete', 'Remove CRM records'),
    ('orders:read', 'View orders and order details'),
    ('orders:write', 'Create and edit draft orders'),
    ('orders:approve', 'Confirm, pack, ship, deliver and cancel orders'),
    ('inventory:read', 'View products, suppliers and stock balances'),
    ('inventory:write', 'Adjust stock, add products and manage suppliers'),
    ('analytics:read', 'View dashboards and export analytics reports'),
    ('tasks:write', 'Create and update workspace tasks and notifications'),
    ('ai:query', 'Ask NEXORA Intelligence operational questions'),
    ('ai:approve', 'Approve AI drafted communications or actions'),
    ('automation:write', 'Create workflows and approve automation executions'),
    ('team:manage', 'Invite members and modify role assignments'),
    ('security:read', 'View audit logs and security telemetry'),
    ('settings:write', 'Modify workspace configuration and integrations')
ON CONFLICT (code) DO NOTHING;

-- Map permissions cleanly to roles
WITH rp(r_code, p_code) AS (
    VALUES
    -- Owner gets all
    ('owner', 'crm:read'), ('owner', 'crm:write'), ('owner', 'crm:delete'),
    ('owner', 'orders:read'), ('owner', 'orders:write'), ('owner', 'orders:approve'),
    ('owner', 'inventory:read'), ('owner', 'inventory:write'), ('owner', 'analytics:read'),
    ('owner', 'tasks:write'), ('owner', 'ai:query'), ('owner', 'ai:approve'),
    ('owner', 'automation:write'), ('owner', 'team:manage'), ('owner', 'security:read'), ('owner', 'settings:write'),
    -- Admin
    ('admin', 'crm:read'), ('admin', 'crm:write'), ('admin', 'crm:delete'),
    ('admin', 'orders:read'), ('admin', 'orders:write'), ('admin', 'orders:approve'),
    ('admin', 'inventory:read'), ('admin', 'inventory:write'), ('admin', 'analytics:read'),
    ('admin', 'tasks:write'), ('admin', 'ai:query'), ('admin', 'ai:approve'),
    ('admin', 'automation:write'), ('admin', 'team:manage'), ('admin', 'security:read'), ('admin', 'settings:write'),
    -- Manager
    ('manager', 'crm:read'), ('manager', 'crm:write'),
    ('manager', 'orders:read'), ('manager', 'orders:write'), ('manager', 'orders:approve'),
    ('manager', 'inventory:read'), ('manager', 'inventory:write'), ('manager', 'analytics:read'),
    ('manager', 'tasks:write'), ('manager', 'ai:query'), ('manager', 'ai:approve'),
    ('manager', 'automation:write'),
    -- Staff
    ('staff', 'crm:read'), ('staff', 'crm:write'),
    ('staff', 'orders:read'), ('staff', 'orders:write'),
    ('staff', 'inventory:read'), ('staff', 'analytics:read'),
    ('staff', 'tasks:write'), ('staff', 'ai:query'),
    -- Viewer
    ('viewer', 'crm:read'), ('viewer', 'orders:read'), ('viewer', 'inventory:read'), ('viewer', 'analytics:read')
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM rp
JOIN roles r ON r.code = rp.r_code
JOIN permissions p ON p.code = rp.p_code
ON CONFLICT DO NOTHING;
