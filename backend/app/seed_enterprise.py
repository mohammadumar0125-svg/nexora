"""Idempotent PostgreSQL seed for the clearly labeled sample evaluation workspace."""
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import owner_engine
from app.core.security import hash_password
from app.services.integrations import DEFAULT_INTEGRATIONS
from sqlalchemy import text

SAMPLE_SLUG = "northbridge-sample-demo"


def _migrate_legacy_sample_workspace(conn) -> Optional[str]:
    """Safely updates any legacy sample workspace records to international sample names without deleting audit logs."""
    legacy_tid = conn.execute(
        text("SELECT id::text FROM tenants WHERE slug = 'singhania-sample-demo' AND is_sample = TRUE")
    ).scalar()
    if not legacy_tid:
        return None

    conn.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": legacy_tid})
    conn.execute(
        text(
            """
            UPDATE tenants
            SET name = 'Northbridge Distribution Co. (Sample)',
                slug = :sl
            WHERE id = :tid
            """
        ),
        {"sl": SAMPLE_SLUG, "tid": legacy_tid},
    )

    user_updates = [
        ("anand@singhaniawholesale.in", "alex@northbridge.example", "Alex Mercer"),
        ("meera.ops@singhaniawholesale.in", "claire.ops@northbridge.example", "Claire Bennett"),
        ("rahul.clerk@singhaniawholesale.in", "david.clerk@northbridge.example", "David Kim"),
        ("audit.viewer@singhaniawholesale.in", "audit.viewer@northbridge.example", "Hannah Brooks"),
    ]
    for old_email, new_email, full_name in user_updates:
        conn.execute(
            text(
                """
                UPDATE users
                SET email = :new_em, full_name = :fn
                WHERE lower(email) = lower(:old_em)
                  AND NOT EXISTS (SELECT 1 FROM users u2 WHERE lower(u2.email) = lower(:new_em))
                """
            ),
            {"old_em": old_email, "new_em": new_email, "fn": full_name},
        )

    customer_updates = [
        (
            "Gupta Kirana Store (Sample)",
            "Harborview Retail Market (Sample)",
            "orders@harborview.sample",
            "+1 415 555 0142",
            "Suite 12, Harbor Market District",
        ),
        (
            "Sharma Supermart (Sample)",
            "Metroline Superstore (Sample)",
            "buy@metroline.sample",
            "+1 415 555 0188",
            "840 Market Avenue, North Hub",
        ),
    ]
    for old_name, new_name, em, ph, addr in customer_updates:
        conn.execute(
            text(
                """
                UPDATE customers
                SET name = :nn, email = :em, phone = :ph, billing_address = :addr
                WHERE tenant_id = :tid AND name = :on
                """
            ),
            {"tid": legacy_tid, "on": old_name, "nn": new_name, "em": em, "ph": ph, "addr": addr},
        )

    contact_updates = [
        ("Ramesh Gupta", "Daniel Carter", "orders@harborview.sample", "+1 415 555 0142"),
        ("Suresh Sharma", "Sophie Laurent", "buy@metroline.sample", "+1 415 555 0188"),
    ]
    for old_fn, new_fn, em, ph in contact_updates:
        conn.execute(
            text(
                """
                UPDATE contacts
                SET full_name = :nfn, email = :em, phone = :ph
                WHERE tenant_id = :tid AND full_name = :ofn
                """
            ),
            {"tid": legacy_tid, "ofn": old_fn, "nfn": new_fn, "em": em, "ph": ph},
        )

    conn.execute(
        text(
            """
            UPDATE leads
            SET company_name = 'Oakridge Fresh Market (Sample)',
                contact_name = 'Liam Carter',
                phone = '+1 415 555 0164'
            WHERE tenant_id = :tid AND contact_name = 'Vikram Joshi'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE leads
            SET title = 'Seasonal Assortment Contract',
                company_name = 'Meridian Grocers (Sample)',
                contact_name = 'Elena Novak',
                phone = '+1 415 555 0195'
            WHERE tenant_id = :tid AND contact_name = 'Anita Kulkarni'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE suppliers
            SET name = 'Pacific Crest Foods Supply Co. (Sample)',
                contact_name = 'Marcus Reid',
                email = 'supply@pacificcrest.sample',
                phone = '+1 415 555 0175',
                address = 'Logistics Park North'
            WHERE tenant_id = :tid AND contact_name = 'Deepak Patil'
            """
        ),
        {"tid": legacy_tid},
    )

    product_updates = [
        ("TEA-RL-250", "TEA-CB-250", "Ceylon Black Tea Carton (24x250g)", "Twinings"),
        ("BIS-PG-140", "BIS-BT-140", "Butter Shortbread Case (48x140g)", "Walkers"),
        ("OIL-DH-10L", "OIL-EV-10L", "Pure Olive Blend Oil 10L Tin", "Meridian Oils"),
        ("DET-SE-1KG", "DET-PD-1KG", "Concentrated Laundry Case (12x1kg)", "ProClean"),
    ]
    for old_sku, new_sku, nm, br in product_updates:
        conn.execute(
            text(
                """
                UPDATE products
                SET sku = :nsku, name = :nm, brand = :br
                WHERE tenant_id = :tid AND sku = :osku
                """
            ),
            {"tid": legacy_tid, "osku": old_sku, "nsku": new_sku, "nm": nm, "br": br},
        )
        conn.execute(
            text(
                """
                UPDATE order_items
                SET sku = :nsku, product_name = :nm
                WHERE tenant_id = :tid AND sku = :osku
                """
            ),
            {"tid": legacy_tid, "osku": old_sku, "nsku": new_sku, "nm": nm},
        )

    conn.execute(
        text(
            """
            UPDATE inventory
            SET location = 'Central Distribution Warehouse'
            WHERE tenant_id = :tid AND location = 'Pune Central Warehouse'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE orders
            SET notes = 'Weekly retail replenishment'
            WHERE tenant_id = :tid AND order_number = 'ORD-00001' AND notes = 'Weekly kirana replenishment'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE orders
            SET source_message = 'Please send 2 cases ProClean concentrated laundry detergent'
            WHERE tenant_id = :tid AND order_number = 'ORD-00002'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE tasks
            SET title = 'Approve ORD-00002 for Metroline Superstore',
                description = 'Confirm stock allocation for ProClean Laundry order.'
            WHERE tenant_id = :tid AND title LIKE '%Sharma Supermart%'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE tasks
            SET title = 'Place reorder PO for Pure Olive Blend Oil 10L'
            WHERE tenant_id = :tid AND title LIKE '%Dhara%'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE notifications
            SET title = 'Low Stock Watch: Pure Olive Blend Oil 10L Tin'
            WHERE tenant_id = :tid AND title LIKE '%Dhara%'
            """
        ),
        {"tid": legacy_tid},
    )
    conn.execute(
        text(
            """
            UPDATE notifications
            SET body = 'Awaiting stock check and confirmation for Metroline Superstore.'
            WHERE tenant_id = :tid AND body LIKE '%Sharma Supermart%'
            """
        ),
        {"tid": legacy_tid},
    )
    return legacy_tid


def seed_sample_workspace() -> None:
    with owner_engine.begin() as conn:
        if _migrate_legacy_sample_workspace(conn):
            return

        existing = conn.execute(
            text("SELECT id::text FROM tenants WHERE slug = :sl"),
            {"sl": SAMPLE_SLUG},
        ).scalar()
        if existing:
            return

        # 1. Create clearly labeled sample tenant
        tid = str(
            conn.execute(
                text(
                    """
                    INSERT INTO tenants (name, slug, currency, timezone, retention_days, tax_id, is_sample)
                    VALUES ('Northbridge Distribution Co. (Sample)', :sl, 'INR', 'Asia/Kolkata', 365, 'TAX-27NB1429Z5', TRUE)
                    RETURNING id::text
                    """
                ),
                {"sl": SAMPLE_SLUG},
            ).scalar()
        )
        conn.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": tid})

        # 2. Seed sample users across roles
        users_spec = [
            ("alex@northbridge.example", "Owner@Nexora2026!", "Alex Mercer", "owner"),
            ("claire.ops@northbridge.example", "Manager@Nexora2026!", "Claire Bennett", "manager"),
            ("david.clerk@northbridge.example", "Clerk@Nexora2026!", "David Kim", "staff"),
            ("audit.viewer@northbridge.example", "Viewer@Nexora2026!", "Hannah Brooks", "viewer"),
        ]
        user_ids = {}
        for email, pwd, full_name, role_code in users_spec:
            uid = conn.execute(
                text("SELECT id::text FROM users WHERE lower(email) = lower(:em)"),
                {"em": email},
            ).scalar()
            if not uid:
                uid = str(
                    conn.execute(
                        text(
                            """
                            INSERT INTO users (email, hashed_password, full_name, is_email_verified, is_active)
                            VALUES (:em, :hpw, :fn, TRUE, TRUE)
                            RETURNING id::text
                            """
                        ),
                        {"em": email, "hpw": hash_password(pwd), "fn": full_name},
                    ).scalar()
                )
            rid = conn.execute(text("SELECT id FROM roles WHERE code = :rc"), {"rc": role_code}).scalar()
            conn.execute(
                text(
                    """
                    INSERT INTO memberships (tenant_id, user_id, role_id, role_code, status)
                    VALUES (:tid, :uid, :rid, :rc, 'active')
                    ON CONFLICT (tenant_id, user_id) DO NOTHING
                    """
                ),
                {"tid": tid, "uid": uid, "rid": rid, "rc": role_code},
            )
            user_ids[role_code] = uid

        owner_id = user_ids["owner"]
        staff_id = user_ids["staff"]

        # 3. Customers & Contacts
        c1 = str(
            conn.execute(
                text(
                    """
                    INSERT INTO customers (tenant_id, name, category, email, phone, gstin, billing_address, owner_user_id, status)
                    VALUES (:tid, 'Harborview Retail Market (Sample)', 'retail', 'orders@harborview.sample', '+1 415 555 0142', 'TAX-98200142', 'Suite 12, Harbor Market District', :uid, 'active')
                    RETURNING id::text
                    """
                ),
                {"tid": tid, "uid": owner_id},
            ).scalar()
        )
        c2 = str(
            conn.execute(
                text(
                    """
                    INSERT INTO customers (tenant_id, name, category, email, phone, gstin, billing_address, owner_user_id, status)
                    VALUES (:tid, 'Metroline Superstore (Sample)', 'wholesale', 'buy@metroline.sample', '+1 415 555 0188', 'TAX-98300188', '840 Market Avenue, North Hub', :uid, 'active')
                    RETURNING id::text
                    """
                ),
                {"tid": tid, "uid": staff_id},
            ).scalar()
        )
        conn.execute(
            text(
                """
                INSERT INTO contacts (tenant_id, customer_id, full_name, email, phone, designation, is_primary)
                VALUES (:tid, :c1, 'Daniel Carter', 'orders@harborview.sample', '+1 415 555 0142', 'Store Proprietor', TRUE),
                       (:tid, :c2, 'Sophie Laurent', 'buy@metroline.sample', '+1 415 555 0188', 'Purchasing Manager', TRUE)
                """
            ),
            {"tid": tid, "c1": c1, "c2": c2},
        )

        # 4. Leads
        conn.execute(
            text(
                """
                INSERT INTO leads (tenant_id, title, company_name, contact_name, phone, source, stage, estimated_value, owner_user_id, next_follow_up_at)
                VALUES
                  (:tid, 'Monthly Beverage Supply Q4', 'Oakridge Fresh Market (Sample)', 'Liam Carter', '+1 415 555 0164', 'referral', 'qualified', 48500.00, :uid, NOW() + INTERVAL '1 day'),
                  (:tid, 'Seasonal Assortment Contract', 'Meridian Grocers (Sample)', 'Elena Novak', '+1 415 555 0195', 'website', 'proposal', 82000.00, :stf, NOW() - INTERVAL '1 day')
                """
            ),
            {"tid": tid, "uid": owner_id, "stf": staff_id},
        )

        # 5. Suppliers, Products & Inventory
        sup_id = str(
            conn.execute(
                text(
                    """
                    INSERT INTO suppliers (tenant_id, name, contact_name, email, phone, address, lead_time_days)
                    VALUES (:tid, 'Pacific Crest Foods Supply Co. (Sample)', 'Marcus Reid', 'supply@pacificcrest.sample', '+1 415 555 0175', 'Logistics Park North', 3)
                    RETURNING id::text
                    """
                ),
                {"tid": tid},
            ).scalar()
        )

        skus = [
            ("TEA-CB-250", "Ceylon Black Tea Carton (24x250g)", "Twinings", "Beverages", "carton", 2400.00, 2050.00, 5.0, 32, 10),
            ("BIS-BT-140", "Butter Shortbread Case (48x140g)", "Walkers", "Biscuits", "carton", 960.00, 810.00, 12.0, 45, 12),
            ("OIL-EV-10L", "Pure Olive Blend Oil 10L Tin", "Meridian Oils", "Oils", "tin", 1850.00, 1620.00, 5.0, 6, 15),
            ("DET-PD-1KG", "Concentrated Laundry Case (12x1kg)", "ProClean", "Home Care", "case", 2280.00, 1980.00, 18.0, 18, 8),
        ]
        prod_ids = {}
        for sku, name, brand, cat, unit, price, cost, tax, qty, thresh in skus:
            pid = str(
                conn.execute(
                    text(
                        """
                        INSERT INTO products (tenant_id, sku, name, brand, category, unit, unit_price, cost_price, tax_rate, supplier_id)
                        VALUES (:tid, :sku, :nm, :br, :cat, :un, :pr, :cp, :tr, :sid)
                        RETURNING id::text
                        """
                    ),
                    {"tid": tid, "sku": sku, "nm": name, "br": brand, "cat": cat, "un": unit, "pr": price, "cp": cost, "tr": tax, "sid": sup_id},
                ).scalar()
            )
            conn.execute(
                text(
                    """
                    INSERT INTO inventory (tenant_id, product_id, quantity_on_hand, reorder_threshold, location)
                    VALUES (:tid, :pid, :qty, :th, 'Central Distribution Warehouse')
                    """
                ),
                {"tid": tid, "pid": pid, "qty": qty, "th": thresh},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO stock_movements (tenant_id, product_id, movement_type, quantity_delta, quantity_after, reference_type, reason, created_by)
                    VALUES (:tid, :pid, 'in', :qty, :qty, 'opening_balance', 'Sample seed opening balance', :uid)
                    """
                ),
                {"tid": tid, "pid": pid, "qty": qty, "uid": owner_id},
            )
            prod_ids[sku] = pid

        # 6. Seed 1 Confirmed Order + 1 Pending Approval Order
        o1 = str(
            conn.execute(
                text(
                    """
                    INSERT INTO orders (tenant_id, order_number, customer_id, status, subtotal, discount_amount, tax_amount, total_amount, inventory_deducted, created_by, approved_by, approved_at, notes)
                    VALUES (:tid, 'ORD-00001', :c1, 'confirmed', 7680.00, 0, 566.40, 8246.40, TRUE, :stf, :own, NOW() - INTERVAL '2 days', 'Weekly retail replenishment')
                    RETURNING id::text
                    """
                ),
                {"tid": tid, "c1": c1, "stf": staff_id, "own": owner_id},
            ).scalar()
        )
        conn.execute(
            text(
                """
                INSERT INTO order_items (tenant_id, order_id, product_id, product_name, sku, quantity, unit_price, tax_rate, line_total)
                VALUES (:tid, :o1, :p1, 'Ceylon Black Tea Carton (24x250g)', 'TEA-CB-250', 2, 2400.00, 5.0, 5040.00),
                       (:tid, :o1, :p2, 'Butter Shortbread Case (48x140g)', 'BIS-BT-140', 3, 960.00, 12.0, 3225.60)
                """
            ),
            {"tid": tid, "o1": o1, "p1": prod_ids["TEA-CB-250"], "p2": prod_ids["BIS-BT-140"]},
        )

        o2 = str(
            conn.execute(
                text(
                    """
                    INSERT INTO orders (tenant_id, order_number, customer_id, status, subtotal, discount_amount, tax_amount, total_amount, due_date, created_by, notes, source_message)
                    VALUES (:tid, 'ORD-00002', :c2, 'pending_approval', 4560.00, 100.00, 820.80, 5280.80, NOW() - INTERVAL '6 hours', :stf, 'Requires manager approval & stock allocation', 'Please send 2 cases ProClean concentrated laundry detergent')
                    RETURNING id::text
                    """
                ),
                {"tid": tid, "c2": c2, "stf": staff_id},
            ).scalar()
        )
        conn.execute(
            text(
                """
                INSERT INTO order_items (tenant_id, order_id, product_id, product_name, sku, quantity, unit_price, tax_rate, line_total)
                VALUES (:tid, :o2, :p4, 'Concentrated Laundry Case (12x1kg)', 'DET-PD-1KG', 2, 2280.00, 18.0, 5380.80)
                """
            ),
            {"tid": tid, "o2": o2, "p4": prod_ids["DET-PD-1KG"]},
        )

        conn.execute(
            text(
                """
                INSERT INTO tenant_counters (tenant_id, counter_name, last_value)
                VALUES (:tid, 'order_number', 2)
                """
            ),
            {"tid": tid},
        )

        # 7. Tasks & Notifications
        conn.execute(
            text(
                """
                INSERT INTO tasks (tenant_id, title, description, priority, status, due_at, assigned_to_user_id, created_by)
                VALUES
                  (:tid, 'Approve ORD-00002 for Metroline Superstore', 'Confirm stock allocation for ProClean Laundry order.', 'high', 'todo', NOW() + INTERVAL '4 hours', :own, :stf),
                  (:tid, 'Place reorder PO for Pure Olive Blend Oil 10L', 'Stock at 6 tins vs threshold 15 tins.', 'urgent', 'in_progress', NOW() + INTERVAL '1 day', :stf, :own)
                """
            ),
            {"tid": tid, "own": owner_id, "stf": staff_id},
        )

        conn.execute(
            text(
                """
                INSERT INTO notifications (tenant_id, user_id, category, title, body)
                VALUES
                  (:tid, NULL, 'low_stock', 'Low Stock Watch: Pure Olive Blend Oil 10L Tin', '6 tins remaining vs reorder threshold of 15 tins.'),
                  (:tid, NULL, 'order', 'Pending Order ORD-00002', 'Awaiting stock check and confirmation for Metroline Superstore.')
                """
            ),
            {"tid": tid},
        )

        # 8. Automation Workflows & Integrations
        wf_id = str(
            conn.execute(
                text(
                    """
                    INSERT INTO automation_workflows (tenant_id, name, description, trigger_event, action_type, action_config_json, requires_approval, is_active, created_by)
                    VALUES (:tid, 'Low-Stock Supplier Reorder Draft', 'Queues human-approved restock reminder whenever SKU crosses threshold.', 'stock_low', 'create_task', '{"task_title": "Review supplier PO for low-stock item"}'::jsonb, TRUE, TRUE, :own)
                    RETURNING id::text
                    """
                ),
                {"tid": tid, "own": owner_id},
            ).scalar()
        )
        conn.execute(
            text(
                """
                INSERT INTO automation_executions (tenant_id, workflow_id, status, trigger_payload_json, result_summary)
                VALUES (:tid, :wid, 'pending_approval', '{"sku": "OIL-EV-10L", "qty": 6}'::jsonb, 'Awaiting manager confirmation before notifying supplier.')
                """
            ),
            {"tid": tid, "wid": wf_id},
        )

        for integ in DEFAULT_INTEGRATIONS:
            conn.execute(
                text(
                    """
                    INSERT INTO integrations (tenant_id, provider_key, category, name, status)
                    VALUES (:tid, :pk, :cat, :nm, 'not_configured')
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"tid": tid, "pk": integ["provider_key"], "cat": integ["category"], "nm": integ["name"]},
            )

        conn.execute(
            text(
                """
                INSERT INTO audit_logs (tenant_id, actor_user_id, action, entity_type, entity_id, after_json)
                VALUES (:tid, :own, 'sample_workspace_seeded', 'tenant', :tid, '{"note": "Sample workspace initialized"}'::jsonb)
                """
            ),
            {"tid": tid, "own": owner_id},
        )


if __name__ == "__main__":
    seed_sample_workspace()
    print("Sample NEXORA Enterprise workspace verified/seeded cleanly.")
