"""Idempotent production bootstrap: apply pending SQL migrations, set DB role
passwords from env, and (optionally) seed the sample workspace.

Runs on every container start. Safe to run repeatedly and concurrently.
Requires MIGRATION_DATABASE_URL (owner connection string).
"""
import os
import secrets
import sys

import psycopg2
from psycopg2 import sql

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MIGRATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "migrations"))


def _dsn() -> str:
    url = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        sys.exit("bootstrap_db: set MIGRATION_DATABASE_URL (owner connection string).")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url.replace("postgresql+psycopg2://", "postgresql://")


def main() -> None:
    conn = psycopg2.connect(_dsn())
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(727274)")  # one bootstrapper at a time
            cur.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "filename TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            )
            conn.commit()
            cur.execute("SELECT filename FROM schema_migrations")
            done = {r[0] for r in cur.fetchall()}
            for fname in sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")):
                if fname in done:
                    continue
                with open(os.path.join(MIGRATIONS_DIR, fname), encoding="utf-8") as fh:
                    cur.execute(fh.read())
                cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (fname,))
                conn.commit()
                print(f"[bootstrap] applied {fname}", flush=True)

            # Migrations create roles with placeholder passwords: replace them.
            api_user = os.getenv("DB_API_USER", "api_role")
            api_pass = os.getenv("DB_API_PASSWORD")
            if not api_pass:
                sys.exit("bootstrap_db: DB_API_PASSWORD must be set in production.")
            cur.execute(sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(sql.Identifier(api_user), sql.Literal(api_pass)))
            worker_pass = os.getenv("DB_WORKER_PASSWORD") or secrets.token_urlsafe(32)
            cur.execute(sql.SQL("ALTER ROLE worker_role WITH PASSWORD {}").format(sql.Literal(worker_pass)))
            conn.commit()
            cur.execute("SELECT pg_advisory_unlock(727274)")
            conn.commit()
        print("[bootstrap] database ready", flush=True)
    finally:
        conn.close()

    if os.getenv("SEED_SAMPLE_WORKSPACE", "true").lower() == "true":
        from app.seed_enterprise import seed_sample_workspace

        seed_sample_workspace()
        print("[bootstrap] sample workspace verified", flush=True)


if __name__ == "__main__":
    main()
