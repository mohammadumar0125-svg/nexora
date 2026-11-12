# Deploying NEXORA to Google Cloud Run & Cloud SQL

This guide describes deploying NEXORA cleanly on **Google Cloud Run**, **Cloud SQL for PostgreSQL 16**, **Cloud Storage**, and **Secret Manager**.

## 1. Infrastructure Components
- **Compute:** Cloud Run container built from root [`Dockerfile`](../Dockerfile) (`deploy/cloudrun.yaml`).
- **Database:** Cloud SQL PostgreSQL 16 instance connected via Cloud SQL Auth Proxy Unix socket. Run SQL migrations cleanly using the administrative owner credential before rolling traffic.
- **Runtime Identity:** Dedicated `nexora_owner` (migrations only) and least-privilege `api_role` (`DATABASE_URL` stored inside GCP Secret Manager).
- **Private Uploads:** Google Cloud Storage bucket with **Public Access Prevention enforced**, set via `STORAGE_BACKEND=gcs` and `GCS_BUCKET_NAME`.

## 2. Deployment Steps
1. Create secrets in GCP Secret Manager:
   - `nexora-api-database-url`: `postgresql://api_role:<STRONG_PASS>@/nexora_enterprise?host=/cloudsql/<PROJECT>:asia-south1:nexora-pg16`
   - `nexora-gemini-api-key`: Server-side Google Gemini API key (if AI synthesis is enabled)
2. Build & push container image to Artifact Registry (`asia-south1-docker.pkg.dev/<PROJECT>/nexora/nexora-enterprise:<TAG>`).
3. Run migration job or initial one-off Cloud Run Job executing:
   - `python3 backend/scripts/setup_postgres.py`
4. Deploy Cloud Run service via `gcloud run services replace deploy/cloudrun.yaml` (substituting `<PROJECT>`, `<IMAGE_TAG>`, and exact allowed `CORS_ORIGINS`).

## 3. Backup, Recovery & Rollback
- **Database Backups:** Enable Cloud SQL automated daily backups and 7-day Point-In-Time Recovery (PITR). Verify quarterly restore drills into a staging instance before deleting pre-migration snapshots.
- **Zero-Downtime Migrations:** Keep schema migrations additive first; retain previous Cloud Run revision (`--no-traffic` canary first) for instant traffic rollback via `gcloud run services update-traffic`.
