# ADR 0003: Postgres-Backed Job Queue with `SKIP LOCKED`

## Status
Accepted

## Context
NEXORA Order Agent offloads all AI processing (Gemini extraction, vector embedding generation) and file exports (CSV generation) to background jobs. We evaluated queue backends:
1. External Redis + Arq / Celery
2. Postgres-backed queue (`background_jobs` table using `FOR UPDATE SKIP LOCKED`)

## Decision
1. **Postgres-Backed Queue:** Implement a transactional queue table `background_jobs` directly in PostgreSQL.
2. **Worker Role & RLS Bypass:**
   - The queue worker connects as `worker_role`.
   - A permissive policy on `background_jobs` allows `worker_role` to claim jobs across all tenants:
     ```sql
     SELECT id, tenant_id, task_name, payload
     FROM background_jobs
     WHERE status = 'queued' AND run_at <= NOW()
     ORDER BY id
     FOR UPDATE SKIP LOCKED
     LIMIT 1;
     ```
   - When a job is claimed, the worker updates `status = 'running'`, `locked_at = NOW()`, `locked_by = <worker_id>`.
   - Before executing the task, the worker establishes tenant RLS context:
     `SET LOCAL app.current_tenant_id = '<job.tenant_id>'`.
3. **Stuck-Job Reclaim:**
   - Jobs stuck in `'running'` with `locked_at < NOW() - INTERVAL '5 minutes'` are automatically reset to `'queued'` (or moved to `'dead_letter'` if `attempts >= max_attempts`).
4. **Zero Extra Infrastructure:**
   - Avoids introducing Redis or Celery broker dependencies.
   - Job enqueueing is transactional: message ingestion and job creation commit atomically.

## Consequences
- ACID guarantees on message intake + task scheduling.
- Simplified operational footprint for Docker Compose and Cloud Run deployments.
- Throughput easily scales to thousands of orders per hour on standard PostgreSQL hardware.
