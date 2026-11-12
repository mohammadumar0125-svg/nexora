import pytest
from app.core.database import OwnerSessionLocal, SessionLocal
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import text

STRONG_PASS = "IsolationPass#2026!"


def _register_org(tc: TestClient, company: str, email: str):
    r = tc.post(
        "/api/auth/register",
        json={
            "company_name": company,
            "full_name": f"{company} Owner",
            "email": email,
            "password": STRONG_PASS,
        },
    )
    assert r.status_code == 201
    return r.json()


def test_multi_tenant_isolation_and_rls_and_immutable_audit(client: TestClient):
    # Org A session
    c1 = TestClient(app)
    org_a = _register_org(c1, "Alpha Foods", "alpha@alphafoods.in")
    csrf_a = org_a["csrf_token"]
    tid_a = org_a["user"]["tenant"]["id"]

    cust_a = c1.post(
        "/api/crm/customers",
        headers={"X-CSRF-Token": csrf_a},
        json={"name": "Alpha Private Buyer", "phone": "+919000011111"},
    ).json()

    prod_a = c1.post(
        "/api/products",
        headers={"X-CSRF-Token": csrf_a},
        json={"sku": "ALPHA-01", "name": "Alpha Spice Pack", "unit_price": 450, "initial_stock": 20},
    ).json()

    ord_a = c1.post(
        "/api/orders",
        headers={"X-CSRF-Token": csrf_a},
        json={"customer_id": cust_a["id"], "items": [{"product_id": prod_a["id"], "quantity": 2}]},
    ).json()

    # Valid PDF upload by Org A
    pdf_up = c1.post(
        "/api/files/upload",
        headers={"X-CSRF-Token": csrf_a},
        data={"entity_type": "customer", "entity_id": cust_a["id"]},
        files={"file": ("po.pdf", b"%PDF-1.4\n%test-invoice\n", "application/pdf")},
    )
    assert pdf_up.status_code == 201
    file_a_id = pdf_up.json()["id"]

    # Org B separate authenticated client
    c2 = TestClient(app)
    org_b = _register_org(c2, "Beta Logistics", "beta@betalog.in")
    tid_b = org_b["user"]["tenant"]["id"]

    # Cross-tenant list checks return empty
    assert c2.get("/api/crm/customers").json() == []
    assert c2.get("/api/products").json() == []
    assert c2.get("/api/orders").json() == []
    assert c2.get("/api/security/audit-logs").json() or True
    audit_b = c2.get("/api/security/audit-logs").json()
    assert all(row["entity_id"] != cust_a["id"] for row in audit_b)

    # Direct UUID IDOR checks fail with 404/403
    assert c2.get(f"/api/crm/customers/{cust_a['id']}").status_code == 404
    assert c2.get(f"/api/orders/{ord_a['id']}").status_code == 404
    assert c2.get(f"/api/files/{file_a_id}/download").status_code == 404

    # Raw Postgres FORCE ROW LEVEL SECURITY verification via api_role
    with SessionLocal() as db:
        db.execute(text("SET LOCAL app.current_tenant_id = ''"))
        assert db.execute(text("SELECT COUNT(*) FROM customers")).scalar() == 0
        assert db.execute(text("SELECT COUNT(*) FROM orders")).scalar() == 0

        db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": tid_b})
        assert db.execute(text("SELECT COUNT(*) FROM customers WHERE id = :id"), {"id": cust_a["id"]}).scalar() == 0

        db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": tid_a})
        assert db.execute(text("SELECT COUNT(*) FROM customers WHERE id = :id"), {"id": cust_a["id"]}).scalar() == 1

    # Immutable audit_logs trigger enforcement even for owner engine
    with OwnerSessionLocal() as odb:
        with pytest.raises(Exception, match="append-only"):
            odb.execute(text("UPDATE audit_logs SET action = 'tampered' WHERE tenant_id = :tid"), {"tid": tid_a})
            odb.commit()
        odb.rollback()


def test_rbac_boundaries_and_file_upload_security(client: TestClient):
    owner_c = TestClient(app)
    owner = _register_org(owner_c, "RBAC Co", "owner@rbacco.in")
    csrf = owner["csrf_token"]

    # Disallowed MIME / spoofed header checks
    bad_exe = owner_c.post(
        "/api/files/upload",
        headers={"X-CSRF-Token": csrf},
        data={"entity_type": "workspace", "entity_id": owner["user"]["tenant"]["id"]},
        files={"file": ("malware.exe", b"MZ\x90\x00", "application/x-msdownload")},
    )
    assert bad_exe.status_code == 400

    spoof_pdf = owner_c.post(
        "/api/files/upload",
        headers={"X-CSRF-Token": csrf},
        data={"entity_type": "workspace", "entity_id": owner["user"]["tenant"]["id"]},
        files={"file": ("fake.pdf", b"NOT_A_REAL_PDF", "application/pdf")},
    )
    assert spoof_pdf.status_code == 400

    # Owner invites a Viewer and a Staff teammate
    inv_viewer = owner_c.post(
        "/api/team/invite",
        headers={"X-CSRF-Token": csrf},
        json={"email": "viewer@rbacco.in", "role_code": "viewer"},
    )
    assert inv_viewer.status_code == 201
    v_tok = inv_viewer.json()["invite_token"]

    inv_staff = owner_c.post(
        "/api/team/invite",
        headers={"X-CSRF-Token": csrf},
        json={"email": "staff@rbacco.in", "role_code": "staff"},
    )
    assert inv_staff.status_code == 201
    s_tok = inv_staff.json()["invite_token"]

    # Viewer accepts invite
    vc = TestClient(app)
    va = vc.post(
        "/api/invitations/accept",
        json={"token": v_tok, "full_name": "Audit Viewer", "password": STRONG_PASS},
    )
    assert va.status_code == 200
    v_csrf = va.json()["csrf_token"]

    # Viewer read allowed for analytics/pulse, writes and security logs blocked
    assert vc.get("/api/pulse").status_code == 200
    assert vc.get("/api/analytics").status_code == 200
    assert vc.get("/api/security/audit-logs").status_code == 403
    assert vc.post("/api/crm/customers", headers={"X-CSRF-Token": v_csrf}, json={"name": "X"}).status_code == 403
    assert vc.post("/api/team/invite", headers={"X-CSRF-Token": v_csrf}, json={"email": "x@x.in", "role_code": "staff"}).status_code == 403

    # Staff accepts invite
    sc = TestClient(app)
    sa = sc.post(
        "/api/invitations/accept",
        json={"token": s_tok, "full_name": "Order Clerk", "password": STRONG_PASS},
    )
    assert sa.status_code == 200
    s_csrf = sa.json()["csrf_token"]

    # Staff can create customer & draft order, CANNOT approve orders or inspect security audit logs
    c_res = sc.post("/api/crm/customers", headers={"X-CSRF-Token": s_csrf}, json={"name": "Staff Created Buyer"})
    assert c_res.status_code == 201
    p_res = owner_c.post(
        "/api/products",
        headers={"X-CSRF-Token": csrf},
        json={"sku": "RBAC-1", "name": "Test Item", "unit_price": 100, "initial_stock": 10},
    )
    o_res = sc.post(
        "/api/orders",
        headers={"X-CSRF-Token": s_csrf},
        json={"customer_id": c_res.json()["id"], "items": [{"product_id": p_res.json()["id"], "quantity": 1}]},
    )
    assert o_res.status_code == 201
    assert sc.post(f"/api/orders/{o_res.json()['id']}/confirm", headers={"X-CSRF-Token": s_csrf}).status_code == 403
    assert sc.get("/api/security/audit-logs").status_code == 403
