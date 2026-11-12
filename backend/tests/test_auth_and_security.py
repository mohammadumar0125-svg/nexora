from app.core.security import compute_totp_code
from fastapi.testclient import TestClient

STRONG_PASS = "StrongPass#2026!"


def test_health_and_security_headers(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "postgresql_connected"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert "default-src 'self'" in resp.headers.get("Content-Security-Policy", "")


def test_public_forms_persist(client: TestClient):
    ea = client.post(
        "/api/public/early-access",
        json={
            "full_name": "Hannah Brooks",
            "email": "hannah@brookstrade.example",
            "company_name": "Brooks Trade Co",
            "business_type": "Wholesale",
            "team_size": "15",
            "notes": "Pilot request",
        },
    )
    assert ea.status_code == 201
    assert ea.json()["status"] == "recorded"

    ct = client.post(
        "/api/public/contact",
        json={
            "name": "Claire Bennett",
            "email": "claire@bennettops.example",
            "company": "Bennett Supply",
            "topic": "Security",
            "message": "Need details on Postgres RLS and GST fields.",
        },
    )
    assert ct.status_code == 201
    assert ct.json()["status"] == "received"


def test_register_csrf_mfa_reset_and_session_revocation(client: TestClient):
    # 1. Weak password rejection
    weak = client.post(
        "/api/auth/register",
        json={
            "company_name": "Acme Traders",
            "full_name": "Liam Carter",
            "email": "liam@acmetraders.example",
            "password": "weak",
        },
    )
    assert weak.status_code == 422 or weak.status_code == 400

    # 2. Valid workspace registration
    reg = client.post(
        "/api/auth/register",
        json={
            "company_name": "Acme Traders",
            "full_name": "Liam Carter",
            "email": "liam@acmetraders.example",
            "password": STRONG_PASS,
        },
    )
    assert reg.status_code == 201
    reg_body = reg.json()
    csrf = reg_body["csrf_token"]
    verify_tok = reg_body["verification_token"]
    assert reg_body["user"]["role_code"] == "owner"

    # 3. Single-use email verification
    v1 = client.post("/api/auth/verify-email", json={"token": verify_tok})
    assert v1.status_code == 200
    v2 = client.post("/api/auth/verify-email", json={"token": verify_tok})
    assert v2.status_code == 400

    # 4. CSRF check on mutating endpoint
    no_csrf = client.post("/api/crm/customers", json={"name": "Blocked Corp"})
    assert no_csrf.status_code == 403

    with_csrf = client.post(
        "/api/crm/customers",
        headers={"X-CSRF-Token": csrf},
        json={"name": "Verified Corp"},
    )
    assert with_csrf.status_code == 201

    # 5. Setup & confirm TOTP MFA
    mfa_setup = client.post("/api/auth/mfa/setup", headers={"X-CSRF-Token": csrf})
    assert mfa_setup.status_code == 200
    secret = mfa_setup.json()["secret"]
    totp = compute_totp_code(secret)
    mfa_conf = client.post(
        "/api/auth/mfa/confirm",
        headers={"X-CSRF-Token": csrf},
        json={"secret": secret, "totp_code": totp},
    )
    assert mfa_conf.status_code == 200

    # 6. Logout and verify MFA gate on login
    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    step1 = client.post(
        "/api/auth/login",
        json={"email": "liam@acmetraders.example", "password": STRONG_PASS},
    )
    assert step1.status_code == 200
    assert step1.json()["mfa_required"] is True

    bad_totp = client.post(
        "/api/auth/login",
        json={"email": "liam@acmetraders.example", "password": STRONG_PASS, "totp_code": "000000"},
    )
    assert bad_totp.status_code == 401

    step2 = client.post(
        "/api/auth/login",
        json={
            "email": "liam@acmetraders.example",
            "password": STRONG_PASS,
            "totp_code": compute_totp_code(secret),
        },
    )
    assert step2.status_code == 200
    assert step2.json()["user"]["mfa_enabled"] is True

    # 7. Forgot & single-use reset password revokes active session
    fg = client.post("/api/auth/forgot-password", json={"email": "liam@acmetraders.example"})
    assert fg.status_code == 200
    reset_tok = fg.json()["dev_reset_token"]
    new_pass = "RotatedPass#2026!"
    rp = client.post(
        "/api/auth/reset-password",
        json={"token": reset_tok, "new_password": new_pass},
    )
    assert rp.status_code == 200
    # Second reuse rejected
    rp2 = client.post(
        "/api/auth/reset-password",
        json={"token": reset_tok, "new_password": new_pass},
    )
    assert rp2.status_code == 400
    # Old cookie must now fail /api/auth/me
    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 401


def test_login_rate_limiting_and_account_lockout(client: TestClient):
    client.post(
        "/api/auth/register",
        json={
            "company_name": "Lock Test Co",
            "full_name": "Test Owner",
            "email": "lock@locktest.in",
            "password": STRONG_PASS,
        },
    )
    # 5 bad logins trigger lockout
    for _ in range(5):
        r = client.post(
            "/api/auth/login",
            json={"email": "lock@locktest.in", "password": "WrongPassword#1"},
        )
        assert r.status_code == 401

    # Even valid password should be rejected during rate-limit lock window
    locked = client.post(
        "/api/auth/login",
        json={"email": "lock@locktest.in", "password": STRONG_PASS},
    )
    assert locked.status_code == 401
