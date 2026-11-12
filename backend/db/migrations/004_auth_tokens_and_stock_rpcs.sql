-- ============================================================================
-- 004_auth_tokens_and_stock_rpcs.sql
-- Hardened single-use auth token RPCs + Deadlock-safe Atomic Stock Order RPCs
-- ============================================================================

-- 1. Password Reset Issue
CREATE OR REPLACE FUNCTION auth_issue_reset_token(p_email TEXT, p_token_hash TEXT)
RETURNS UUID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    v_user_id UUID;
BEGIN
    SELECT id INTO v_user_id FROM users WHERE lower(email) = lower(trim(p_email)) AND is_active = TRUE;
    IF v_user_id IS NULL THEN
        RETURN NULL;
    END IF;

    -- Invalidate unused previous password reset tokens
    UPDATE auth_tokens SET used_at = NOW()
    WHERE user_id = v_user_id AND token_type = 'password_reset' AND used_at IS NULL;

    INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at)
    VALUES (v_user_id, 'password_reset', p_token_hash, NOW() + INTERVAL '30 minutes');

    RETURN v_user_id;
END;
$$;

-- 2. Password Reset Consume (revokes ALL active sessions cleanly)
CREATE OR REPLACE FUNCTION auth_consume_reset_token(p_token_hash TEXT, p_new_hashed_password TEXT)
RETURNS UUID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    v_tok auth_tokens%ROWTYPE;
BEGIN
    SELECT * INTO v_tok FROM auth_tokens
    WHERE token_hash = p_token_hash
      AND token_type = 'password_reset'
      AND used_at IS NULL
      AND expires_at > NOW()
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reset token is invalid or expired';
    END IF;

    UPDATE auth_tokens SET used_at = NOW() WHERE id = v_tok.id;
    UPDATE users SET hashed_password = p_new_hashed_password, failed_login_attempts = 0, locked_until = NULL, updated_at = NOW()
    WHERE id = v_tok.user_id;
    UPDATE sessions SET revoked_at = NOW() WHERE user_id = v_tok.user_id AND revoked_at IS NULL;

    RETURN v_tok.user_id;
END;
$$;

-- 3. Email Verification Consume
CREATE OR REPLACE FUNCTION auth_consume_email_verify_token(p_token_hash TEXT)
RETURNS UUID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    v_tok auth_tokens%ROWTYPE;
BEGIN
    SELECT * INTO v_tok FROM auth_tokens
    WHERE token_hash = p_token_hash
      AND token_type = 'email_verify'
      AND used_at IS NULL
      AND expires_at > NOW()
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Verification token is invalid or expired';
    END IF;

    UPDATE auth_tokens SET used_at = NOW() WHERE id = v_tok.id;
    UPDATE users SET is_email_verified = TRUE, updated_at = NOW() WHERE id = v_tok.user_id;

    RETURN v_tok.user_id;
END;
$$;

-- 4. Update User Password + Revoke Other Sessions
CREATE OR REPLACE FUNCTION auth_change_user_password(p_user_id UUID, p_new_hashed_password TEXT, p_keep_session_id UUID DEFAULT NULL)
RETURNS VOID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE users SET hashed_password = p_new_hashed_password, updated_at = NOW() WHERE id = p_user_id;
    UPDATE sessions SET revoked_at = NOW()
    WHERE user_id = p_user_id AND revoked_at IS NULL AND (p_keep_session_id IS NULL OR id <> p_keep_session_id);
END;
$$;

-- 5. Configure MFA (TOTP) Secret
CREATE OR REPLACE FUNCTION auth_configure_mfa(p_user_id UUID, p_enabled BOOLEAN, p_secret TEXT)
RETURNS VOID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE users SET mfa_enabled = p_enabled, mfa_secret = p_secret, updated_at = NOW()
    WHERE id = p_user_id;
END;
$$;

-- 6. Deadlock-Safe Atomic Order Confirmation + Inventory Deduction
CREATE OR REPLACE FUNCTION confirm_order_atomic(
    p_tenant_id UUID,
    p_order_id UUID,
    p_actor_user_id UUID
)
RETURNS TABLE (
    order_id UUID,
    order_status VARCHAR(32),
    total_amount NUMERIC(12, 2)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_ord orders%ROWTYPE;
    v_item RECORD;
    v_inv inventory%ROWTYPE;
    v_new_qty NUMERIC(12, 4);
BEGIN
    SELECT * INTO v_ord FROM orders
    WHERE id = p_order_id AND tenant_id = p_tenant_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found in tenant';
    END IF;

    IF v_ord.status NOT IN ('draft', 'pending_approval') THEN
        RAISE EXCEPTION 'Order cannot be confirmed from status %', v_ord.status;
    END IF;

    IF NOT v_ord.inventory_deducted THEN
        -- Lock inventory rows in deterministic product_id order to eliminate deadlocks
        FOR v_item IN
            SELECT oi.product_id, oi.product_name, SUM(oi.quantity) AS req_qty
            FROM order_items oi
            WHERE oi.tenant_id = p_tenant_id AND oi.order_id = p_order_id
            GROUP BY oi.product_id, oi.product_name
            ORDER BY oi.product_id ASC
        LOOP
            SELECT * INTO v_inv FROM inventory
            WHERE tenant_id = p_tenant_id AND product_id = v_item.product_id
            FOR UPDATE;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Inventory record missing for product %', v_item.product_name;
            END IF;

            IF v_inv.quantity_on_hand < v_item.req_qty THEN
                RAISE EXCEPTION 'Insufficient stock for % (available: %, requested: %)',
                    v_item.product_name, v_inv.quantity_on_hand, v_item.req_qty;
            END IF;

            v_new_qty := v_inv.quantity_on_hand - v_item.req_qty;

            UPDATE inventory
            SET quantity_on_hand = v_new_qty,
                updated_at = NOW()
            WHERE id = v_inv.id;

            INSERT INTO stock_movements (
                tenant_id, product_id, movement_type, quantity_delta, quantity_after,
                reference_type, reference_id, reason, created_by
            ) VALUES (
                p_tenant_id, v_item.product_id, 'order_deduct', -v_item.req_qty, v_new_qty,
                'order', p_order_id, 'Confirmed order ' || v_ord.order_number, p_actor_user_id
            );

            IF v_new_qty <= v_inv.reorder_threshold THEN
                INSERT INTO notifications (
                    tenant_id, user_id, category, title, body, entity_type, entity_id
                ) VALUES (
                    p_tenant_id, NULL, 'low_stock',
                    'Low Stock Alert: ' || v_item.product_name,
                    format('Remaining stock %s is at/below reorder threshold %s after %s.', v_new_qty, v_inv.reorder_threshold, v_ord.order_number),
                    'product', v_item.product_id
                );
            END IF;
        END LOOP;
    END IF;

    UPDATE orders
    SET status = 'confirmed',
        inventory_deducted = TRUE,
        approved_by = p_actor_user_id,
        approved_at = NOW(),
        updated_at = NOW()
    WHERE id = p_order_id AND tenant_id = p_tenant_id;

    INSERT INTO audit_logs (
        tenant_id, actor_user_id, action, entity_type, entity_id, after_json
    ) VALUES (
        p_tenant_id, p_actor_user_id, 'order_confirmed', 'order', p_order_id::text,
        jsonb_build_object('order_number', v_ord.order_number, 'status', 'confirmed', 'total_amount', v_ord.total_amount)
    );

    RETURN QUERY SELECT v_ord.id, 'confirmed'::varchar(32), v_ord.total_amount;
END;
$$;

-- 7. Atomic Order Cancellation + Inventory Restoration
CREATE OR REPLACE FUNCTION cancel_order_atomic(
    p_tenant_id UUID,
    p_order_id UUID,
    p_actor_user_id UUID,
    p_reason TEXT DEFAULT 'Cancelled by authorized operator'
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_ord orders%ROWTYPE;
    v_item RECORD;
    v_inv inventory%ROWTYPE;
    v_new_qty NUMERIC(12, 4);
BEGIN
    SELECT * INTO v_ord FROM orders
    WHERE id = p_order_id AND tenant_id = p_tenant_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found in tenant';
    END IF;

    IF v_ord.status IN ('delivered', 'cancelled') THEN
        RAISE EXCEPTION 'Order in status % cannot be cancelled', v_ord.status;
    END IF;

    IF v_ord.inventory_deducted THEN
        FOR v_item IN
            SELECT oi.product_id, SUM(oi.quantity) AS req_qty
            FROM order_items oi
            WHERE oi.tenant_id = p_tenant_id AND oi.order_id = p_order_id
            GROUP BY oi.product_id
            ORDER BY oi.product_id ASC
        LOOP
            SELECT * INTO v_inv FROM inventory
            WHERE tenant_id = p_tenant_id AND product_id = v_item.product_id
            FOR UPDATE;

            v_new_qty := v_inv.quantity_on_hand + v_item.req_qty;
            UPDATE inventory SET quantity_on_hand = v_new_qty, updated_at = NOW() WHERE id = v_inv.id;

            INSERT INTO stock_movements (
                tenant_id, product_id, movement_type, quantity_delta, quantity_after,
                reference_type, reference_id, reason, created_by
            ) VALUES (
                p_tenant_id, v_item.product_id, 'order_restore', v_item.req_qty, v_new_qty,
                'order', p_order_id, p_reason, p_actor_user_id
            );
        END LOOP;
    END IF;

    UPDATE orders
    SET status = 'cancelled',
        inventory_deducted = FALSE,
        updated_at = NOW()
    WHERE id = p_order_id AND tenant_id = p_tenant_id;

    INSERT INTO audit_logs (
        tenant_id, actor_user_id, action, entity_type, entity_id, after_json
    ) VALUES (
        p_tenant_id, p_actor_user_id, 'order_cancelled', 'order', p_order_id::text,
        jsonb_build_object('order_number', v_ord.order_number, 'reason', p_reason)
    );
END;
$$;

REVOKE ALL ON FUNCTION auth_issue_reset_token(TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_issue_reset_token(TEXT, TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_consume_reset_token(TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_consume_reset_token(TEXT, TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_consume_email_verify_token(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_consume_email_verify_token(TEXT) TO api_role;

REVOKE ALL ON FUNCTION auth_change_user_password(UUID, TEXT, UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_change_user_password(UUID, TEXT, UUID) TO api_role;

REVOKE ALL ON FUNCTION auth_configure_mfa(UUID, BOOLEAN, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_configure_mfa(UUID, BOOLEAN, TEXT) TO api_role;

REVOKE ALL ON FUNCTION confirm_order_atomic(UUID, UUID, UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION confirm_order_atomic(UUID, UUID, UUID) TO api_role;

REVOKE ALL ON FUNCTION cancel_order_atomic(UUID, UUID, UUID, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cancel_order_atomic(UUID, UUID, UUID, TEXT) TO api_role;
