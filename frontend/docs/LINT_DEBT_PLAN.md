# Frontend Lint Debt Cleanup Plan

## Baseline (current)
- Command: `pnpm lint`
- Snapshot: **147 issues** (0 errors, 147 warnings)
- Primary categories:
  - `@typescript-eslint/no-explicit-any`
  - `react-hooks/exhaustive-deps`
  - `react-refresh/only-export-components`
  - `@typescript-eslint/no-unsafe-function-type`

## Goals
1. Keep lint debt visible and measurable on every PR.
2. Reduce the current debt incrementally without blocking critical releases.
3. Prevent new lint regressions from being introduced.

## Phased execution

### Phase 1: Stop regression (CI now)
- Keep lint running in CI and publish issue counts in job summary.
- Fail CI only on **new errors** in touched files.
- Keep warnings non-blocking until debt is reduced.

### Phase 2: High-risk fixes first
- Replace `any` in API/transaction/auth surfaces.
- Fix `exhaustive-deps` warnings where stale closures can cause runtime bugs.
- Resolve `Function` typing usage in socket/event handlers.

### Phase 3: Structure and DX cleanup
- Split non-component exports from component files for fast-refresh rules.
- Add shared utility types to avoid repeated inline `any` fallbacks.
- Tighten ESLint config to treat key rules as errors after debt drops.

## Suggested sprint target
- Sprint A: cut warnings by ~30% (focus: services + hooks + auth)
- Sprint B: cut warnings by another ~30% (focus: dashboard + trading)
- Sprint C: finish remaining warnings and enforce stricter lint gates

## Commands
- `pnpm lint`
- `pnpm lint:fix`
- `pnpm type-check`
