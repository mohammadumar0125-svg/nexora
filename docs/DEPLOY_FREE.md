# Free deploy: Render (app) + Neon (database)

Cost: $0. Trade-offs: the app sleeps after ~15 min idle (first visit then takes ~1 min); Neon DB sleeps after 5 min idle (adds ~1 s).

## 1. Database (Neon)
1. Sign up at neon.com (free, no card) -> create a project.
2. Click **Connect**, turn **off** "Connection pooling", copy the connection string
   (looks like `postgresql://neondb_owner:...@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`).

## 2. Code on GitHub
Push this folder (the one containing `Dockerfile` and `render.yaml`) to a GitHub repo.

## 3. App (Render)
1. render.com -> **New -> Blueprint** -> pick your repo.
2. When asked, paste the Neon string into **MIGRATION_DATABASE_URL**. (Optional: GEMINI_API_KEY.)
3. Apply. First build takes ~5-8 min. On boot the app creates all tables/roles itself.
4. Open `https://<your-service>.onrender.com/api/health` -> must show `"status":"healthy"`.

## Notes
- Do NOT set `DATABASE_URL` on Render; it is derived automatically.
- Demo login (sample workspace): `alex@northbridge.example` / `Owner@Nexora2026!`.
  These passwords are public in the repo. Set `SEED_SAMPLE_WORKSPACE=false` for a real launch.
- Don't use Render's own free Postgres: it is deleted after 30 days.
- Uploaded files are stored on disk and are lost on every restart on the free plan.
