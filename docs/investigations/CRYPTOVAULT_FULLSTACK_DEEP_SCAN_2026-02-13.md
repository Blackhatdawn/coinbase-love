# CryptoVault Full-Stack Deep Scan (2026-02-13)

## Scope
- Backend: FastAPI routers, services, environment/config, deployment config.
- Frontend: React pages/services/runtime config and integration patterns.
- Deployment/config artifacts: `render.yaml`, backend env templates.

## What is currently working / implemented
1. **Core backend API is actively mounted and structured for production endpoints** (auth, wallet, trading, crypto, alerts, notifications, transfers, users, monitoring, versioning, config). Archived routes are intentionally left as no-op placeholders for backward compatibility.
2. **Runtime config handshake is implemented end-to-end**: backend exposes `/api/config`, frontend consumes it with fallback/degraded state handling and normalizes URL/path behavior.
3. **Cross-origin auth/session wiring is in place**: backend CORS allows credentials and frontend uses credentials on API/socket calls.
4. **Operational hardening exists**: request IDs, security headers, timeout middleware, optional advanced rate limiter/CSRF middleware, gzip, health endpoints.
5. **Critical deployment config exists for Render** with explicit env var matrix for DB/auth/CORS/public URLs/cache/monitoring/payment/email.

## What appears unimplemented / partially implemented
1. **Notifications WebSocket token handling has an acknowledged TODO** (comment indicates JWT handling still needs production-grade improvement).
2. **P2P transfer email notifications are not implemented yet** (explicit TODO in wallet transfer flow).
3. **Frontend FAQ resources/blog block is placeholder-only** (“coming soon”).
4. **Frontend Contact page live chat is placeholder-only** (Intercom integration TODO + disabled button).
5. **Order share UX is placeholder-only** (“Share feature coming soon”).
6. **Referrals page currently uses in-file mock referral records** instead of backend data integration.
7. **Earn page currently uses mock active staking data**.

## Features configured but effectively not live / potentially misleading
1. **Render deploy config sets `EMAIL_SERVICE=mock`**, so production email verification flows run in mocked mode unless changed.
2. **Auth signup logic auto-verifies users when email is mock**, meaning verification UX/security differs from true transactional-email mode.
3. **NOWPayments service automatically falls back to mock mode without API key**, so deposit/payment behavior can appear functional while not truly integrated.
4. **Feature flags (`FEATURE_*`) are present in deployment and `.env.example` but are not consumed in app logic (based on repository search),** suggesting they are either legacy placeholders or planned-but-unwired toggles.

## Configuration drift / cleanup risks found
1. **`backend/.env.example` appears outdated relative to the live backend config model**:
   - Uses PostgreSQL-style `DATABASE_URL`, pool vars, and legacy keys not represented by the active `Settings` model.
   - Active backend config expects MongoDB-centric keys (`MONGO_URL`, `DB_NAME`, etc.).
2. **`/api/config` returns hardcoded version `1.0.0`** while deployment/config references `2.0.0`; this can produce frontend display/telemetry inconsistencies.

## Recommended next actions (priority)
1. Implement P2P transfer email notifications and remove TODO.
2. Replace mock data sources on Referrals/Earn pages with authenticated backend endpoints.
3. Decide whether `FEATURE_*` flags are real; either wire them through config + guards or remove from deployment/env examples.
4. Update `backend/.env.example` to match actual `Settings` schema to reduce operator misconfiguration risk.
5. Replace `/api/config` hardcoded version with `settings.app_version`.
6. Move contact live chat and FAQ/blog placeholders to tracked tasks with owners/dates.

## Evidence map
- Backend app routing/middleware and archived placeholders: `backend/server.py`
- Runtime config backend: `backend/routers/config.py`
- Runtime config frontend: `frontend/src/lib/runtimeConfig.ts`
- Deployment env and mock-mode defaults: `render.yaml`
- Auth auto-verify behavior in mock email mode: `backend/routers/auth.py`
- NOWPayments mock fallback: `backend/nowpayments_service.py`
- Unimplemented TODOs/placeholders:
  - `backend/routers/notifications.py`
  - `backend/routers/wallet.py`
  - `frontend/src/pages/FAQ.tsx`
  - `frontend/src/pages/Contact.tsx`
  - `frontend/src/components/OrderConfirmationModal.tsx`
  - `frontend/src/pages/Referrals.tsx`
  - `frontend/src/pages/Earn.tsx`
- Config drift candidate: `backend/.env.example`, `backend/config.py`
