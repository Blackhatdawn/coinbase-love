# CryptoVault Full-Stack Sync Scan (2026-02-14)

## Scope
- Frontend ↔ backend API contract alignment scan.
- Static implementation-completeness scan for production readiness.
- Build/compile sanity checks.

## High-level status
- **API contract coverage:** Frontend `apiClient` static `/api/*` endpoints map to backend routers (no exact-path misses found in static scan).
- **Build health:** Frontend production build succeeds; backend modules compile.
- **Readiness:** Core flows exist, but there are still several **partially implemented** or **misconfigured behavior gates** that should be addressed for true production completeness.

## Findings

### 1) Transfer feature flag is wired to the wrong setting
- **Severity:** High
- **Type:** Bug / Misconfiguration
- **Symptom:** P2P transfer endpoint can be disabled when withdrawals are disabled, even if transfers should be independently controlled.
- **Evidence:** `create_p2p_transfer` checks `feature_withdrawals_enabled` instead of a transfer-specific flag. (`backend/routers/wallet.py`)
- **Root cause:** Transfer flow reuses withdrawal feature gate.
- **Recommended fix:** Introduce `FEATURE_TRANSFERS_ENABLED` in backend config/env templates and gate `/wallet/transfer` with that setting.

### 2) Contact form is still frontend-only (no backend submission path)
- **Severity:** Medium
- **Type:** Unimplemented feature
- **Symptom:** Contact form submit handler logs to console and resets form; no API integration.
- **Evidence:** `handleSubmit` only does `console.log` with a comment indicating backend integration is pending. (`frontend/src/pages/Contact.tsx`)
- **Root cause:** UI shipped without backend route/service binding.
- **Recommended fix:** Add `/api/contact` endpoint with validation/rate-limits + email/ticket integration; wire page to `apiClient` and success/error toasts.

### 3) Earn page still references mock variable in APY metric
- **Severity:** High
- **Type:** Bug / Incomplete migration from mock data
- **Symptom:** Avg APY card computes from `mockActiveStakes` while page otherwise uses live `positionsData`.
- **Evidence:** Avg APY formula references `mockActiveStakes` directly. (`frontend/src/pages/Earn.tsx`)
- **Root cause:** Partial refactor from mock data to API-backed data.
- **Recommended fix:** Replace with `activeStakes`-based reducer and zero-safe denominator guard.

### 4) Referrals summary endpoint has deployment URL drift risk
- **Severity:** Medium
- **Type:** Misconfiguration risk
- **Symptom:** Referral link base URL is hardcoded.
- **Evidence:** `app_url = "https://www.cryptovault.financial"` in referrals summary router. (`backend/routers/referrals.py`)
- **Root cause:** Static domain in backend response logic.
- **Recommended fix:** Use `settings.app_url` (or equivalent runtime config) for consistency across environments.

### 5) Recommended setup flow still includes explicit “coming soon” action
- **Severity:** Low
- **Type:** UX completeness gap
- **Symptom:** "Connect Mobile App" setup card has `action: null` with "Coming soon" comment.
- **Evidence:** Setup options include null action for mobile app step. (`frontend/src/components/RecommendedSetup.tsx`)
- **Root cause:** Intentional placeholder not replaced with real flow/CTA.
- **Recommended fix:** Replace with waitlist/modal deep-link, or hide unavailable option behind feature flag.

### 6) Login verification rule comment and behavior mismatch
- **Severity:** Low
- **Type:** Maintainability / Policy clarity
- **Symptom:** Comment says verification is skipped when email service mocked or dev mode, but code skips verification for any non-production env.
- **Evidence:** `skip_verification = (settings.environment != 'production')`. (`backend/routers/auth.py`)
- **Root cause:** Policy changed without updating comment/explicit logic.
- **Recommended fix:** Clarify intended policy and align code + comment; if strict staging checks are desired, gate by explicit env values.

### 7) Earn backend endpoint is minimal and lacks lifecycle operations
- **Severity:** Medium
- **Type:** Partially implemented feature
- **Symptom:** `/earn` exposes only products/positions reads; no create/close stake operations or reward accrual workflows.
- **Evidence:** Router has only `GET /products` and `GET /positions`. (`backend/routers/earn.py`)
- **Root cause:** Dashboard data plumbing implemented, full earn domain not yet implemented.
- **Recommended fix:** Add stake create/redeem endpoints + transaction ledger integration + APY source governance.

## Frontend ↔ Backend sync check details
- Static endpoint extraction found no direct `/api/*` path mismatches between `frontend/src/lib/apiClient.ts` and backend routers.
- Sync risk remains in **response-shape semantics** for newer endpoints (e.g., Earn/referrals), where frontend assumptions should be covered by contract tests.

## Recommended next actions (priority order)
1. Fix transfer feature-gating (`FEATURE_TRANSFERS_ENABLED`) and deploy env updates.
2. Fix Earn Avg APY metric to remove residual mock variable usage.
3. Replace hardcoded referrals URL with runtime setting.
4. Implement contact form backend integration with anti-abuse controls.
5. Add contract tests for `earn` and `referrals` response shapes.
6. Complete Earn lifecycle operations (stake/redeem/reward accounting).

## Validation commands used in this scan
- `rg -n "TODO|FIXME|..." backend frontend -S`
- `rg -n "apiClient\.(get|post|...)\('/api/" frontend/src -S`
- `rg -n "APIRouter\(|@router\.(get|post|...)\(" backend/routers -S`
- `python -m compileall backend`
- `pnpm -C frontend build`
