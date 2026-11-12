-- ============================================================================
-- Allow the migration/owner role (whoever runs these migrations) to pass FORCE RLS.
-- Needed on managed Postgres (Render, Neon, ...) where the owner is NOT a superuser
-- and has no BYPASSRLS. The SECURITY DEFINER auth functions and the seed script run
-- as this owner. The API itself connects as api_role, which stays fully tenant-isolated.
-- ============================================================================
DO $$
DECLARE
    tbl TEXT;
    owner_name TEXT := current_user;
BEGIN
    FOR tbl IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relrowsecurity
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS nexora_owner_admin ON %I;', tbl);
        EXECUTE format(
            'CREATE POLICY nexora_owner_admin ON %I AS PERMISSIVE FOR ALL TO %I USING (true) WITH CHECK (true);',
            tbl, owner_name
        );
    END LOOP;
END $$;
