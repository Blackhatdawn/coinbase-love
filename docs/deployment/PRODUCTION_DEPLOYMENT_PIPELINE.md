# Production Deployment Pipeline

This repo now deploys frontend and backend independently for safer production releases.

## Frontend (Vercel)
Workflow: `.github/workflows/vercel-frontend-deploy.yml`

### Trigger
- Push to `main` or `production` with frontend-related file changes.
- Manual run (`workflow_dispatch`).

### Required GitHub Secrets
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

### What it does
1. Installs frontend dependencies with pnpm.
2. Runs type-check and production build.
3. Pulls Vercel production environment.
4. Builds with `vercel build` and deploys prebuilt output to production.

## Backend (Render)
Workflow: `.github/workflows/deploy.yml` (`deploy-staging` and `deploy-production` jobs)

### Trigger
- `main` branch deploys staging backend.
- `production` branch deploys production backend.

### Required GitHub Secrets
- `RENDER_API_KEY`
- `RENDER_STAGING_BACKEND_ID`
- `RENDER_PROD_BACKEND_ID`

### Optional GitHub Variables
- `STAGING_BACKEND_HEALTHCHECK_URL` (default: `https://cryptovault-api-staging.onrender.com/health`)
- `PROD_BACKEND_HEALTHCHECK_URL` (default: `https://cryptovault-api.onrender.com/health`)

### What it does
1. Triggers backend deploy via Render API.
2. Runs retry-based smoke health checks.
3. Fails workflow if backend cannot recover within retry window.

## Recommended rollout
1. Merge backend changes to `main` and confirm staging health checks.
2. Merge frontend changes (or deploy frontend-only) and verify Vercel production.
3. Promote backend to `production` branch when staging is stable.
