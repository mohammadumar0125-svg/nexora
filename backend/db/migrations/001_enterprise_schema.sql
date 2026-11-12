-- ============================================================================
-- NEXORA Enterprise SaaS Platform - Unified PostgreSQL 16 Schema (Stage 3-8)
-- Covers all 26 core entities + security, privacy, intake, and public intake
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. TENANTS, USERS, ROLES, PERMISSIONS, MEMBERSHIPS, INVITATIONS, SESSIONS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    currency VARCHAR(12) NOT NULL DEFAULT 'INR',
    timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Kolkata',
    retention_days INT NOT NULL DEFAULT 365 CHECK (retention_days >= 30 AND retention_days <= 3650),
    tax_id VARCHAR(64) DEFAULT '',
    is_sample BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret VARCHAR(128),
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (lower(email));

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(40) UNIQUE NOT NULL,
    name VARCHAR(80) NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(80) UNIQUE NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    role_code VARCHAR(40) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_memberships_tenant_user UNIQUE (tenant_id, user_id),
    CONSTRAINT uq_memberships_tenant_id UNIQUE (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships (user_id);

CREATE TABLE IF NOT EXISTS invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role_code VARCHAR(40) NOT NULL CHECK (role_code IN ('owner', 'admin', 'manager', 'staff', 'viewer')),
    invited_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'revoked', 'expired')),
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_invitations_tenant ON invitations (tenant_id);

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash VARCHAR(64) UNIQUE NOT NULL,
    csrf_token VARCHAR(64) NOT NULL,
    ip_address VARCHAR(64) NOT NULL DEFAULT '',
    user_agent VARCHAR(255) NOT NULL DEFAULT '',
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_sessions_membership FOREIGN KEY (tenant_id, user_id) REFERENCES memberships(tenant_id, user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at);

CREATE TABLE IF NOT EXISTS auth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_type VARCHAR(32) NOT NULL CHECK (token_type IN ('password_reset', 'email_verify')),
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS login_rate_limits (
    id BIGSERIAL PRIMARY KEY,
    limit_key VARCHAR(255) UNIQUE NOT NULL,
    attempts INT NOT NULL DEFAULT 1,
    first_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    locked_until TIMESTAMPTZ
);

-- ----------------------------------------------------------------------------
-- 2. CRM MODULE: CUSTOMERS, CONTACTS, LEADS, ACTIVITIES, NOTES, ALIASES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'wholesale',
    email VARCHAR(255) DEFAULT '',
    phone VARCHAR(64) DEFAULT '',
    gstin VARCHAR(32) DEFAULT '',
    billing_address TEXT DEFAULT '',
    owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'prospect', 'inactive')),
    language_hints VARCHAR(64) DEFAULT 'en,hi',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_customers_tenant_id UNIQUE (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS idx_customers_tenant_name ON customers (tenant_id, name);

CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) DEFAULT '',
    phone VARCHAR(64) DEFAULT '',
    designation VARCHAR(120) DEFAULT '',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_contacts_customer FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT uq_contacts_tenant_id UNIQUE (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) DEFAULT '',
    email VARCHAR(255) DEFAULT '',
    phone VARCHAR(64) DEFAULT '',
    source VARCHAR(80) NOT NULL DEFAULT 'direct',
    stage VARCHAR(40) NOT NULL DEFAULT 'new' CHECK (stage IN ('new', 'contacted', 'qualified', 'proposal', 'won', 'lost')),
    estimated_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (estimated_value >= 0),
    owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    customer_id UUID,
    next_follow_up_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_leads_customer FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, id) ON DELETE SET NULL,
    CONSTRAINT uq_leads_tenant_id UNIQUE (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS idx_leads_tenant_stage ON leads (tenant_id, stage);

CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(40) NOT NULL CHECK (entity_type IN ('customer', 'lead', 'order', 'task')),
    entity_id UUID NOT NULL,
    activity_type VARCHAR(40) NOT NULL CHECK (activity_type IN ('note', 'call', 'email', 'meeting', 'follow_up', 'system')),
    summary TEXT NOT NULL,
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_activities_entity ON activities (tenant_id, entity_type, entity_id);

CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(40) NOT NULL,
    entity_id UUID NOT NULL,
    body TEXT NOT NULL,
    author_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notes_entity ON notes (tenant_id, entity_type, entity_id);

-- ----------------------------------------------------------------------------
-- 3. PRODUCTS, SUPPLIERS, INVENTORY, STOCK MOVEMENTS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) DEFAULT '',
    email VARCHAR(255) DEFAULT '',
    phone VARCHAR(64) DEFAULT '',
    address TEXT DEFAULT '',
    lead_time_days INT NOT NULL DEFAULT 5 CHECK (lead_time_days >= 0),
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_suppliers_tenant_id UNIQUE (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(120) DEFAULT '',
    category VARCHAR(120) NOT NULL DEFAULT 'General',
    unit VARCHAR(40) NOT NULL DEFAULT 'unit',
    unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (unit_price >= 0),
    cost_price NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (cost_price >= 0),
    tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 5.00 CHECK (tax_rate >= 0 AND tax_rate <= 100),
    supplier_id UUID,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_products_supplier FOREIGN KEY (tenant_id, supplier_id) REFERENCES suppliers(tenant_id, id) ON DELETE SET NULL,
    CONSTRAINT uq_products_tenant_sku UNIQUE (tenant_id, sku),
    CONSTRAINT uq_products_tenant_id UNIQUE (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity_on_hand NUMERIC(12, 4) NOT NULL DEFAULT 0 CHECK (quantity_on_hand >= 0),
    reserved_quantity NUMERIC(12, 4) NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    reorder_threshold NUMERIC(12, 4) NOT NULL DEFAULT 10 CHECK (reorder_threshold >= 0),
    location VARCHAR(120) NOT NULL DEFAULT 'Main Warehouse',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_inventory_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT uq_inventory_tenant_product UNIQUE (tenant_id, product_id)
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    movement_type VARCHAR(32) NOT NULL CHECK (movement_type IN ('in', 'out', 'adjustment', 'order_deduct', 'order_restore')),
    quantity_delta NUMERIC(12, 4) NOT NULL,
    quantity_after NUMERIC(12, 4) NOT NULL CHECK (quantity_after >= 0),
    reference_type VARCHAR(40) DEFAULT '',
    reference_id UUID,
    reason TEXT DEFAULT '',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_movements_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_movements_product ON stock_movements (tenant_id, product_id, created_at DESC);

CREATE TABLE IF NOT EXISTS customer_aliases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    product_id UUID NOT NULL,
    phrase VARCHAR(255) NOT NULL,
    source VARCHAR(40) NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_aliases_customer FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_aliases_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT uq_customer_alias_phrase UNIQUE (tenant_id, customer_id, phrase)
);

-- ----------------------------------------------------------------------------
-- 4. ORDERS & ORDER ITEMS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_counters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    counter_name VARCHAR(64) NOT NULL,
    last_value BIGINT NOT NULL DEFAULT 0,
    CONSTRAINT uq_tenant_counter UNIQUE (tenant_id, counter_name)
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    order_number VARCHAR(64) NOT NULL,
    customer_id UUID NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_approval', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled')),
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (discount_amount >= 0),
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (tax_amount >= 0),
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0),
    due_date TIMESTAMPTZ,
    notes TEXT DEFAULT '',
    source_message TEXT DEFAULT '',
    inventory_deducted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_orders_customer FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_orders_tenant_number UNIQUE (tenant_id, order_number),
    CONSTRAINT uq_orders_tenant_id UNIQUE (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS idx_orders_tenant_status ON orders (tenant_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    quantity NUMERIC(12, 4) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (tax_rate >= 0),
    line_total NUMERIC(12, 2) NOT NULL CHECK (line_total >= 0),
    CONSTRAINT fk_order_items_order FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 5. WORKSPACE, TASKS, NOTIFICATIONS, AUTOMATION, AI, AUDIT, INTEGRATIONS, FILES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    priority VARCHAR(24) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR(24) NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done')),
    due_at TIMESTAMPTZ,
    assigned_to_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    entity_type VARCHAR(40) DEFAULT '',
    entity_id UUID,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tasks_tenant_status ON tasks (tenant_id, status, due_at);

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(40) NOT NULL DEFAULT 'system',
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    entity_type VARCHAR(40) DEFAULT '',
    entity_id UUID,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications (tenant_id, user_id, is_read, created_at DESC);

CREATE TABLE IF NOT EXISTS automation_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    trigger_event VARCHAR(80) NOT NULL,
    condition_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    action_type VARCHAR(80) NOT NULL,
    action_config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_workflows_tenant_id UNIQUE (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS automation_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    workflow_id UUID NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending_approval' CHECK (status IN ('pending_approval', 'executed', 'failed', 'rejected')),
    trigger_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_summary TEXT DEFAULT '',
    retry_count INT NOT NULL DEFAULT 0,
    error_message TEXT DEFAULT '',
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    CONSTRAINT fk_executions_workflow FOREIGN KEY (tenant_id, workflow_id) REFERENCES automation_workflows(tenant_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    interaction_type VARCHAR(40) NOT NULL DEFAULT 'qa' CHECK (interaction_type IN ('qa', 'summary', 'draft', 'extraction', 'recommendation')),
    prompt TEXT NOT NULL,
    sanitized_prompt TEXT NOT NULL,
    response_text TEXT NOT NULL,
    grounded_sources_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    provider_mode VARCHAR(40) NOT NULL DEFAULT 'grounded_sql',
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(32) NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'pending_approval', 'approved', 'rejected', 'error')),
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(60) NOT NULL DEFAULT '',
    entity_id VARCHAR(100) NOT NULL DEFAULT '',
    before_json JSONB,
    after_json JSONB,
    ip_address VARCHAR(64) DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_created ON audit_logs (tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    provider_key VARCHAR(64) NOT NULL,
    category VARCHAR(40) NOT NULL CHECK (category IN ('email', 'messaging', 'payments', 'accounting', 'crm', 'api')),
    name VARCHAR(120) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'not_configured' CHECK (status IN ('configured', 'not_configured', 'disabled')),
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tenant_integration UNIQUE (tenant_id, provider_key)
);

CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(40) NOT NULL,
    entity_id UUID NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    mime_type VARCHAR(120) NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
    sha256 VARCHAR(64) NOT NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 6. PUBLIC WEBSITE LEADS (EARLY ACCESS & CONTACT FORMS)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public_early_access_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    business_type VARCHAR(120) DEFAULT '',
    team_size VARCHAR(40) DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public_contact_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    company VARCHAR(255) DEFAULT '',
    topic VARCHAR(120) NOT NULL DEFAULT 'General',
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
