"""Apply PostgreSQL migrations for nexora_enterprise and nexora_enterprise_test."""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

MIGRATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "migrations"))
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_SUPERUSER = os.getenv("POSTGRES_ADMIN_USER", "nexora_owner")
PG_SUPERPASS = os.getenv("POSTGRES_ADMIN_PASSWORD", "nexora_owner_secret")
TARGET_DBS = [
    os.getenv("POSTGRES_DB", "nexora_enterprise"),
    os.getenv("POSTGRES_TEST_DB", "nexora_enterprise_test"),
]


def ensure_database(db_name: str) -> None:
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_SUPERUSER,
        password=PG_SUPERPASS,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{db_name}" OWNER "{PG_SUPERUSER}";')
            print(f"Created PostgreSQL database: {db_name}")
    conn.close()


def apply_migrations(db_name: str) -> None:
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_SUPERUSER,
        password=PG_SUPERPASS,
        dbname=db_name,
    )
    sql_files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
    try:
        with conn:
            with conn.cursor() as cur:
                for fname in sql_files:
                    fpath = os.path.join(MIGRATIONS_DIR, fname)
                    with open(fpath, "r", encoding="utf-8") as fh:
                        cur.execute(fh.read())
                    print(f"[{db_name}] Applied {fname}")
    finally:
        conn.close()


if __name__ == "__main__":
    for target_db in TARGET_DBS:
        ensure_database(target_db)
        apply_migrations(target_db)
    print("PostgreSQL migrations completed cleanly.")
