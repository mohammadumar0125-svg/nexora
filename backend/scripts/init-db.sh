#!/usr/bin/env bash
set -e

# Reads passwords from environment or falls back to secure defaults
API_PASS="${DB_API_PASSWORD:-api_secret_pass}"
WORKER_PASS="${DB_WORKER_PASSWORD:-worker_secret_pass}"
AUTH_PASS="${DB_AUTH_DEFINER_PASSWORD:-auth_secret_pass}"
DB_NAME="${POSTGRES_DB:-nexora}"
OWNER_USER="${POSTGRES_USER:-nexora_owner}"

echo ">>> Initializing NEXORA Database Roles for '${DB_NAME}'..."

psql -v ON_ERROR_STOP=1 --username "$OWNER_USER" --dbname "$DB_NAME" <<-EOSQL
    -- 1. Enable Required Extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "vector";

    -- 2. Create Roles with credentials from env
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_role') THEN
            CREATE ROLE api_role WITH LOGIN PASSWORD '${API_PASS}';
        ELSE
            ALTER ROLE api_role WITH PASSWORD '${API_PASS}';
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'worker_role') THEN
            CREATE ROLE worker_role WITH LOGIN PASSWORD '${WORKER_PASS}';
        ELSE
            ALTER ROLE worker_role WITH PASSWORD '${WORKER_PASS}';
        END IF;

        -- auth_definer is strictly NOLOGIN (it only owns the SECURITY DEFINER function)
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_definer') THEN
            CREATE ROLE auth_definer WITH NOLOGIN;
        END IF;
    END \$\$;

    -- 3. Schema Usage
    GRANT USAGE ON SCHEMA public TO api_role, worker_role, auth_definer;

    -- 4. Set Default Privileges FOR ROLE nexora_owner
    -- Tables created by nexora_owner will automatically grant operational access
    ALTER DEFAULT PRIVILEGES FOR ROLE ${OWNER_USER} IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_role;

    ALTER DEFAULT PRIVILEGES FOR ROLE ${OWNER_USER} IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO api_role;

    ALTER DEFAULT PRIVILEGES FOR ROLE ${OWNER_USER} IN SCHEMA public
        GRANT SELECT, UPDATE ON TABLES TO worker_role;

    ALTER DEFAULT PRIVILEGES FOR ROLE ${OWNER_USER} IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO worker_role;

    -- Note: Worker role has NO default INSERT on future tables (opt-in only)
    -- and explicitly NO access to users
EOSQL

echo ">>> NEXORA Database Roles initialized successfully."
