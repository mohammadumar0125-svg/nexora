import os
import sys

# Configure isolated PostgreSQL test database BEFORE importing app modules
os.environ["POSTGRES_DB"] = os.getenv("POSTGRES_TEST_DB", "nexora_enterprise_test")
os.environ["APP_ENV"] = "development"
os.environ["GEMINI_API_KEY"] = ""
os.environ["STORAGE_BACKEND"] = "local"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psycopg2
import pytest
from app.core.database import OwnerSessionLocal
from app.core.rate_limit import _API_BUCKETS
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import text

MIGRATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "migrations"))


@pytest.fixture(scope="session", autouse=True)
def ensure_test_migrations():
    """Ensures nexora_enterprise_test exists and all SQL migrations are applied."""
    db_name = os.environ["POSTGRES_DB"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "nexora_owner")
    password = os.getenv("POSTGRES_PASSWORD", "nexora_owner_secret")

    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db_name)
    sql_files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
    try:
        with conn:
            with conn.cursor() as cur:
                for fname in sql_files:
                    with open(os.path.join(MIGRATIONS_DIR, fname), "r", encoding="utf-8") as fh:
                        cur.execute(fh.read())
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def clean_postgres_db():
    """Truncates all workspace & auth data cleanly before each test without removing roles/permissions."""
    _API_BUCKETS.clear()
    with OwnerSessionLocal() as db:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    public_early_access_requests,
                    public_contact_messages,
                    audit_logs,
                    ai_interactions,
                    automation_executions,
                    automation_workflows,
                    files,
                    integrations,
                    notifications,
                    tasks,
                    order_items,
                    orders,
                    stock_movements,
                    inventory,
                    products,
                    suppliers,
                    customer_aliases,
                    notes,
                    activities,
                    leads,
                    contacts,
                    customers,
                    invitations,
                    sessions,
                    auth_tokens,
                    login_rate_limits,
                    memberships,
                    tenant_counters,
                    users,
                    tenants
                RESTART IDENTITY CASCADE
                """
            )
        )
        db.commit()
    yield


@pytest.fixture()
def client():
    with TestClient(app) as tc:
        yield tc
