# NEXORA — The Next Generation Business Developer

**One intelligent workspace to help growing businesses manage relationships, daily operations, orders, inventory, analytics, team collaboration and human-controlled automation.**

Built initially for Indian SMEs (retail, distribution, local wholesale and service teams) on a clean multi-tenant PostgreSQL architecture ready for international expansion.

---

## Architecture Summary

| Layer | Technology | Highlights |
| --- | --- | --- |
| **Frontend (Public + Private App)** | React 18, TypeScript, Tailwind CSS, Framer Motion, React Router v6 | Light enterprise theme (`#F6F7F3`, `#183D32`, `#D9F36A`), Sora & Inter typography, 18 public marketing/legal/auth routes + 17 workspace modules |
| **Backend API** | FastAPI + SQLAlchemy Core + Uvicorn | 82 registered routes across public forms, enterprise auth, CRM, orders, inventory, analytics, tasks, notifications, files, AI, automation & security |
| **Database & Tenant Isolation** | Unified PostgreSQL 16 | Least-privilege `api_role`, `FORCE ROW LEVEL SECURITY` scoped by `app.current_tenant_id`, append-only `audit_logs`, deadlock-safe atomic order stock RPCs |
| **Auth & Security** | Argon2id, HttpOnly Cookies, CSRF Token, TOTP MFA | Rate-limited logins, session revocation, single-use reset/verify tokens, magic-byte file verification, strict CSP/OWASP security headers |
| **AI Intelligence** | Grounded SQL Context + Optional Google Gemini (`google-genai`) | Server-side API key isolation, grounded source table citations, prompt-injection detection, approval gate for drafts |

---

## Local Development & Verification Setup

### 1. Prerequisites
- Python `3.9+`
- Node.js `20+`
- Local PostgreSQL `16+` running on `localhost:5432`

### 2. Provision PostgreSQL 16 Schema & Seed Sample Workspace
```bash
cd backend
../venv/bin/python scripts/setup_postgres.py
../venv/bin/python app/seed_enterprise.py
```

Default evaluation credentials seeded strictly under the **explicitly labeled sample workspace (`Singhania & Sons Distributors (Sample)`)**:
- Owner: `anand@singhaniawholesale.in` / `Owner@Nexora2026!`
- Manager: `meera.ops@singhaniawholesale.in` / `Manager@Nexora2026!`
- Staff: `rahul.clerk@singhaniawholesale.in` / `Clerk@Nexora2026!`
- Viewer: `audit.viewer@singhaniawholesale.in` / `Viewer@Nexora2026!`

### 3. Build Frontend & Run Unified Server
```bash
cd frontend
npm ci && npm run build
cd ..
./start.sh
```
Access both the **Public Corporate Website (`http://127.0.0.1:8000/`)** and **Private Enterprise Application (`http://127.0.0.1:8000/app`)** from one origin.

### 4. Automated Test Suites
```bash
# Backend integration, RLS, CSRF, MFA, concurrency & E2E tests against nexora_enterprise_test
cd backend && ../venv/bin/pytest -v && ../venv/bin/ruff check app tests

# Frontend unit/component & 18-route sweep tests + TypeScript check
cd frontend && npm test && npm run build
```

---

## Documentation
- [Google Cloud Run Deployment Guide](docs/DEPLOYMENT_GCP.md)
- [Security & Privacy Review](docs/SECURITY_REVIEW.md)
