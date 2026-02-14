# Render Python 3.11 Runtime + Clean Deploy Checklist

Use this runbook when Render deploys with the wrong Python runtime or appears to ignore `PYTHON_VERSION`.

## 1) Explicitly pin Python to 3.11.x

1. In Render Dashboard, open backend service **Settings**.
2. Set **Python Version** to **3.11** (or 3.11.x if shown).
3. Keep `PYTHON_VERSION=3.11.11` in environment variables as a compatibility fallback.
4. This repository also pins runtime with `backend/.python-version` (`3.11.11`).

## 2) If `PYTHON_VERSION` is ignored

Render can prioritize runtime selection from service settings and project files.

Use these in order:

1. **Render runtime setting** (`Settings -> Python Version = 3.11`).
2. **`backend/.python-version`** with `3.11.11`.
3. Keep env var `PYTHON_VERSION=3.11.11` as an additional fallback.

## 3) Trigger a clean deploy

1. Go to **Manual Deploy**.
2. Click **Clear build cache & deploy** (wording may vary by UI version).
3. Wait for build and start phases to complete.

## 4) Validate in logs + health endpoint

In Render logs, confirm startup line from `backend/start_server.py`:

- Expected log snippet: `[startup] Python: 3.11...`

Then verify health endpoint:

```bash
curl -fsS https://cryptovault-api.onrender.com/health
```

Expected: HTTP 200 and JSON body with `"status": "healthy"`.

## Quick log filters

Search for these markers in Render logs:

- `[startup] Python:`
- `[startup] Event loop:`
- `Uvicorn running on`

If Python is not 3.11, re-check Settings runtime version and redeploy with cache clear again.
