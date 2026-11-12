-- Migration: 001_initial_schema.sql
-- Description: Core schema, composite FKs, PERMISSIVE RLS, triggers, and permissions.

-- ============================================================================
-- 1. EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- 2. TABLES & COMPOSITE MULTI-TENANT CONSTRAINTS
-- ============================================================================

-- 2.1 Tenants
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.2 Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'clerk')),
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_users_tenant_id UNIQUE (tenant_id, id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_lower_email ON users (lower(email));

-- 2.3 Tenant Counters (Monotonic tenant-scoped order numbers)
CREATE TABLE IF NOT EXISTS tenant_counters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    counter_name VARCHAR(50) NOT NULL,
    last_value BIGINT NOT NULL DEFAULT 0,
    CONSTRAINT uq_tenant_counter UNIQUE (tenant_id, counter_name),
    CONSTRAINT uq_tenant_counters_tenant_id UNIQUE (tenant_id, id)
);

-- 2.4 Retailers
CREATE TABLE IF NOT EXISTS retailers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    address TEXT,
    language_hint VARCHAR(50) DEFAULT 'en,hi',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_retailers_tenant_id UNIQUE (tenant_id, id)
);

-- 2.5 Products Master (Never hard deleted; active=false for soft delete)
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(100),
    size VARCHAR(100),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_products_code_per_tenant UNIQUE (tenant_id, code),
    CONSTRAINT uq_products_tenant_id UNIQUE (tenant_id, id)
);

-- 2.6 Product Units
CREATE TABLE IF NOT EXISTS product_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    unit VARCHAR(50) NOT NULL,
    base_qty NUMERIC(12, 4) NOT NULL,
    is_base_unit BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_product_units_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_product_unit UNIQUE (product_id, unit),
    CONSTRAINT uq_product_units_tenant_id UNIQUE (tenant_id, id)
);

-- 2.7 Product Stock & Base Prices
CREATE TABLE IF NOT EXISTS product_stock_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    base_unit VARCHAR(50) NOT NULL,
    stock NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    base_price NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_stock_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_stock_product UNIQUE (product_id),
    CONSTRAINT uq_product_stock_prices_tenant_id UNIQUE (tenant_id, id)
);

-- 2.8 Product Embeddings
CREATE TABLE IF NOT EXISTS product_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-004',
    embedding vector(768) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_embeddings_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_embedding_product UNIQUE (product_id),
    CONSTRAINT uq_product_embeddings_tenant_id UNIQUE (tenant_id, id)
);

-- 2.9 Retailer Learned Shorthand
CREATE TABLE IF NOT EXISTS retailer_aliases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    retailer_id UUID NOT NULL,
    phrase VARCHAR(255) NOT NULL,
    product_id UUID NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'clerk_correction',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_aliases_retailer FOREIGN KEY (tenant_id, retailer_id) REFERENCES retailers(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_aliases_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_retailer_phrase UNIQUE (retailer_id, phrase),
    CONSTRAINT uq_retailer_aliases_tenant_id UNIQUE (tenant_id, id)
);

-- 2.10 Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    retailer_id UUID NOT NULL,
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('paste', 'whatsapp', 'pdf', 'audio')),
    raw_text TEXT NOT NULL,
    dedup_hash VARCHAR(64) NOT NULL,
    file_path TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'processed', 'failed', 'duplicate', 'needs_manual_entry')),
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_messages_retailer FOREIGN KEY (tenant_id, retailer_id) REFERENCES retailers(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_messages_tenant_id UNIQUE (tenant_id, id)
);

-- 2.11 Extraction Runs
CREATE TABLE IF NOT EXISTS extraction_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    message_id UUID NOT NULL,
    model VARCHAR(100) NOT NULL,
    schema_version VARCHAR(50) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    raw_json TEXT NOT NULL,
    tokens_used INT DEFAULT 0,
    latency_ms INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_extractions_message FOREIGN KEY (tenant_id, message_id) REFERENCES messages(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT uq_extraction_runs_tenant_id UNIQUE (tenant_id, id)
);

-- 2.12 Order Drafts
CREATE TABLE IF NOT EXISTS order_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    message_id UUID UNIQUE NOT NULL,
    retailer_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'needs_review', 'ready_to_approve', 'approved', 'rejected')),
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_drafts_message FOREIGN KEY (tenant_id, message_id) REFERENCES messages(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_drafts_retailer FOREIGN KEY (tenant_id, retailer_id) REFERENCES retailers(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_order_drafts_tenant_id UNIQUE (tenant_id, id)
);

-- 2.13 Order Lines
CREATE TABLE IF NOT EXISTS order_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    draft_id UUID NOT NULL,
    line_number INT NOT NULL,
    phrase VARCHAR(255) NOT NULL,
    qty NUMERIC(10, 2) NULL,            -- NULLABLE, NO DEFAULT (R1: never guess)
    unit VARCHAR(50) NULL,              -- NULLABLE, NO DEFAULT
    product_id UUID NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('green', 'yellow', 'red')),
    original_status VARCHAR(20) NOT NULL CHECK (original_status IN ('green', 'yellow', 'red')),
    score NUMERIC(5, 4) NOT NULL DEFAULT 0.0,
    match_layer VARCHAR(50),
    reason TEXT NOT NULL,
    candidates_json JSONB DEFAULT '[]'::jsonb,
    source_char_start INT,
    source_char_end INT,
    resolved_by UUID NULL,
    resolved_at TIMESTAMPTZ NULL,
    CONSTRAINT fk_lines_draft FOREIGN KEY (tenant_id, draft_id) REFERENCES order_drafts(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_lines_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_lines_resolved_by FOREIGN KEY (tenant_id, resolved_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_order_lines_tenant_id UNIQUE (tenant_id, id)
);

-- 2.14 Clarifications
CREATE TABLE IF NOT EXISTS clarifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    line_id UUID NOT NULL,
    draft_text TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'answered')),
    proposed_product_id UUID NULL,
    sent_by UUID NULL,
    sent_at TIMESTAMPTZ NULL,
    answer TEXT NULL,
    answered_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_clarifications_line FOREIGN KEY (tenant_id, line_id) REFERENCES order_lines(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_clarifications_sent_by FOREIGN KEY (tenant_id, sent_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_clarifications_proposed_product FOREIGN KEY (tenant_id, proposed_product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_clarifications_tenant_id UNIQUE (tenant_id, id)
);

-- 2.15 Orders
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    draft_id UUID UNIQUE NOT NULL,
    order_number VARCHAR(100) NOT NULL,
    approved_by UUID NOT NULL,
    approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    item_count INT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'confirmed',
    CONSTRAINT fk_orders_draft FOREIGN KEY (tenant_id, draft_id) REFERENCES order_drafts(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_orders_approved_by FOREIGN KEY (tenant_id, approved_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_tenant_order_number UNIQUE (tenant_id, order_number),
    CONSTRAINT uq_orders_tenant_id UNIQUE (tenant_id, id)
);

-- 2.16 Order Items (Immutable historic snapshot at approval)
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    qty NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    line_total NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_items_order FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_order_items_tenant_id UNIQUE (tenant_id, id)
);

-- 2.17 Exports
CREATE TABLE IF NOT EXISTS exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    order_id UUID NOT NULL,
    format VARCHAR(50) NOT NULL DEFAULT 'csv',
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    file_path TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_exports_order FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id) ON DELETE CASCADE,
    CONSTRAINT uq_exports_tenant_id UNIQUE (tenant_id, id)
);

-- 2.18 Append-Only Audit Log
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    actor_type VARCHAR(50) NOT NULL CHECK (actor_type IN ('user', 'ai', 'system')),
    actor_id UUID NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    before_state JSONB DEFAULT '{}'::jsonb,
    after_state JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_audit_events_tenant_id UNIQUE (tenant_id, id)
);

-- 2.19 Background Jobs
CREATE TABLE IF NOT EXISTS background_jobs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    queue_name VARCHAR(100) NOT NULL DEFAULT 'default',
    task_name VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'dead_letter')),
    attempts INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 3,
    locked_at TIMESTAMPTZ NULL,
    locked_by VARCHAR(255) NULL,
    last_error TEXT NULL,
    run_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_background_jobs_tenant_id UNIQUE (tenant_id, id)
);

-- ============================================================================
-- 3. INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_drafts_tenant_status_created ON order_drafts (tenant_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_lines_draft_id ON order_lines (draft_id);
CREATE INDEX IF NOT EXISTS idx_lines_tenant_draft ON order_lines (tenant_id, draft_id);
CREATE INDEX IF NOT EXISTS idx_messages_dedup ON messages (tenant_id, retailer_id, dedup_hash, received_at);
CREATE INDEX IF NOT EXISTS idx_clarifications_line_id ON clarifications (line_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_jobs_claim ON background_jobs (status, queue_name, run_at) WHERE status IN ('queued', 'running');
CREATE INDEX IF NOT EXISTS idx_product_embeddings_hnsw ON product_embeddings USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- 4. DATABASE TRIGGER: APPROVAL GATE ENFORCEMENT (R2)
-- ============================================================================
CREATE OR REPLACE FUNCTION check_order_approval_gate()
RETURNS TRIGGER AS $$
DECLARE
    v_red_count INT;
    v_null_item_count INT;
    v_draft_status VARCHAR(50);
BEGIN
    SELECT status INTO v_draft_status
    FROM order_drafts
    WHERE id = NEW.draft_id AND tenant_id = NEW.tenant_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Approval blocked: Order draft % not found for tenant %', NEW.draft_id, NEW.tenant_id;
    END IF;

    -- Block if ANY red lines remain
    SELECT COUNT(*) INTO v_red_count
    FROM order_lines
    WHERE draft_id = NEW.draft_id AND tenant_id = NEW.tenant_id AND status = 'red';

    IF v_red_count > 0 THEN
        RAISE EXCEPTION 'Approval blocked: Draft contains % RED line(s) requiring clerk resolution.', v_red_count;
    END IF;

    -- Block if ANY line is missing product_id, qty, or unit
    SELECT COUNT(*) INTO v_null_item_count
    FROM order_lines
    WHERE draft_id = NEW.draft_id AND tenant_id = NEW.tenant_id
      AND (product_id IS NULL OR qty IS NULL OR unit IS NULL);

    IF v_null_item_count > 0 THEN
        RAISE EXCEPTION 'Approval blocked: Draft contains % line(s) with missing product, quantity, or unit.', v_null_item_count;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_enforce_order_approval_gate ON orders;
CREATE TRIGGER trg_enforce_order_approval_gate
    BEFORE INSERT ON orders
    FOR EACH ROW
    EXECUTE FUNCTION check_order_approval_gate();

-- ============================================================================
-- 5. ROW-LEVEL SECURITY (RLS) POLICIES (PERMISSIVE)
-- ============================================================================

-- 5.1 Tenants table: Isolated so api_role and worker_role can only see their own tenant
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_self_policy ON tenants;
CREATE POLICY tenant_self_policy ON tenants
    AS PERMISSIVE
    FOR ALL
    TO api_role, worker_role
    USING (id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 5.2 All Tenant-Scoped Tables
DO $$
DECLARE
    tbl text;
    tables text[] := ARRAY[
        'users', 'tenant_counters', 'retailers', 'products', 'product_units', 'product_stock_prices',
        'product_embeddings', 'retailer_aliases', 'messages', 'extraction_runs',
        'order_drafts', 'order_lines', 'clarifications', 'orders', 'order_items',
        'exports', 'audit_events'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', tbl);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY;', tbl);
        
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_policy ON %I;', tbl);
        
        EXECUTE format('
            CREATE POLICY tenant_isolation_policy ON %I
            AS PERMISSIVE
            FOR ALL
            TO api_role, worker_role
            USING (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid);
        ', tbl);
    END LOOP;
END $$;

-- 5.3 Background jobs queue RLS
ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_jobs FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS jobs_api_tenant_policy ON background_jobs;
CREATE POLICY jobs_api_tenant_policy ON background_jobs
    AS PERMISSIVE
    FOR ALL
    TO api_role
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

DROP POLICY IF EXISTS worker_cross_tenant_jobs_policy ON background_jobs;
CREATE POLICY worker_cross_tenant_jobs_policy ON background_jobs
    AS PERMISSIVE
    FOR ALL
    TO worker_role
    USING (true)
    WITH CHECK (true);

-- 5.4 Auth Definer Policy on Users
DROP POLICY IF EXISTS auth_definer_user_lookup_policy ON users;
CREATE POLICY auth_definer_user_lookup_policy ON users
    AS PERMISSIVE
    FOR SELECT
    TO auth_definer
    USING (true);

-- ============================================================================
-- 6. SECURITY DEFINER AUTH FUNCTION
-- ============================================================================
CREATE OR REPLACE FUNCTION lookup_user_for_auth(p_email TEXT)
RETURNS TABLE (
    user_id UUID,
    tenant_id UUID,
    hashed_password VARCHAR(255),
    role VARCHAR(50),
    name VARCHAR(255),
    is_active BOOLEAN
)
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.tenant_id, u.hashed_password, u.role, u.name, u.is_active
    FROM users u
    WHERE lower(u.email) = lower(p_email) AND u.is_active = TRUE;
END;
$$;

ALTER FUNCTION lookup_user_for_auth(TEXT) OWNER TO auth_definer;
REVOKE ALL ON FUNCTION lookup_user_for_auth(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION lookup_user_for_auth(TEXT) TO api_role;

-- ============================================================================
-- 7. ROLE PRIVILEGES & IMMUTABILITY ENFORCEMENT
-- ============================================================================

-- api_role grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO api_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_role;

-- Enforce Audit & History Immutability on api_role
REVOKE UPDATE, DELETE ON order_items FROM api_role;
REVOKE DELETE ON orders FROM api_role;
REVOKE UPDATE, DELETE ON messages FROM api_role;
GRANT UPDATE (status) ON messages TO api_role; -- Only status can be updated (e.g. processed/duplicate)

-- worker_role grants
GRANT SELECT, INSERT, UPDATE, DELETE ON background_jobs TO worker_role;
GRANT SELECT, INSERT, UPDATE ON messages, extraction_runs, order_drafts, order_lines, clarifications, exports, product_embeddings TO worker_role;
GRANT SELECT ON products, product_units, product_stock_prices, retailers, retailer_aliases, tenants TO worker_role;
GRANT SELECT ON orders, order_items TO worker_role; -- For bill-ready CSV export generation!
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO worker_role;

-- worker_role REVOKES (Strict R2 & Security)
REVOKE SELECT ON users FROM worker_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON orders, order_items FROM worker_role;

-- auth_definer grants
GRANT SELECT ON users TO auth_definer;

-- Audit Events: INSERT and SELECT only; NO UPDATE, DELETE, TRUNCATE
GRANT INSERT, SELECT ON audit_events TO api_role, worker_role;
REVOKE UPDATE, DELETE, TRUNCATE ON audit_events FROM api_role, worker_role, PUBLIC;
