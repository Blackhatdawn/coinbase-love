# Production Deployment Pipeline

This repository now uses separate deployment pipelines for frontend (Vercel) and backend (Render). This is the production-standard setup for reducing blast radius and avoiding cross-service deploy failures.

## What was not production-standard (and now fixed)

1. Frontend and backend deployment paths were still partially coupled.
2. Backend deploys depended on frontend test/image pipeline completion.
3. Frontend workflow deployed production from both `main` and `production` (too risky for stable production promotion).
4. Vercel CLI was unpinned (`latest`), which can introduce sudden breakages.
5. Pipelines had no concurrency control, so overlapping commits could race deployments.
6. Render/Vercel secret presence was not pre-validated, causing avoidable runtime failures.

## Frontend pipeline (Vercel)
Workflow: `.github/workflows/vercel-frontend-deploy.yml`

### Trigger
- Push to `main` or `production` for frontend-related changes.
- Manual run via `workflow_dispatch`.

### Behavior
- `main` branch deploys **preview**.
- `production` branch deploys **production**.

### Required GitHub Secrets
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

### Checks included
1. Secret presence validation.
2. Frontend install with frozen lockfile.
3. Type-check and production build before deploy.
4. Deterministic Vercel CLI version (`39.1.0`).
5. Branch-safe deploy behavior: `main` = preview, `production` = production only.
6. Concurrency guard prevents overlapping deploys per branch.

## Backend pipeline (Render)
Workflow: `.github/workflows/deploy.yml`

### Trigger
- Push to `main` or `production` with backend/deploy-file changes.
- Manual run via `workflow_dispatch`.

### Required GitHub Secrets
- `RENDER_API_KEY`
- `RENDER_STAGING_BACKEND_ID`
- `RENDER_PROD_BACKEND_ID`

### Optional GitHub Variables
- `STAGING_BACKEND_HEALTHCHECK_URL` (default: `https://cryptovault-api-staging.onrender.com/health`)
- `PROD_BACKEND_HEALTHCHECK_URL` (default: `https://cryptovault-api.onrender.com/health`)

### Checks included
1. Backend-only security scan (`backend/` scope).
2. Backend lint and tests.
3. Backend-only Docker image build/push.
4. Retry-based health check validation after Render deployment trigger.
5. Preflight secret checks for Render API key and service IDs.
6. Concurrency guard prevents overlapping backend deploys per branch.

## Recommended release flow
1. Merge backend changes to `main` and confirm staging health checks pass.
2. Merge frontend changes to `main` and validate preview deploy.
3. Promote frontend/backend to `production` branch for production rollout.


## Current production backend target
- Base URL: `https://cryptovault-api.onrender.com`
- Render service ID: `srv-d5j1ttfpm1nc73fk1l8g`

Set these in repository secrets/variables so workflow deploy targets and smoke checks stay aligned.


## Render uvloop startup error fix
If Render logs show `ModuleNotFoundError: No module named "uvloop"` on Python 3.13, use these safeguards:
- Set `UVICORN_LOOP=asyncio` in Render environment.
- Pin runtime via `PYTHON_VERSION=3.11.11` (until all deps are verified on 3.13).
- Start with `python start_server.py` (already configured) so loop fallback logic is applied.
