# Validation and CI Runbook

## Local Validation Commands

From project root:

```bash
pnpm exec tsc --noEmit
pnpm exec eslint app lib components --max-warnings 0
pytest -q backend/tests
```

## CI Workflow

Workflow file: `.github/workflows/ci.yml`

Jobs:

- `frontend`
  - Install dependencies
  - Type-check
  - Lint app/lib/components
- `backend`
  - Install Python dependencies
  - Run backend integration tests (`backend/tests`)

## Release Gate

Before merge/deploy:

1. `ci.yml` green on PR.
2. `/api/chat/providers` includes expected provider health state.
3. Core chat path tested with `provider=auto`.
4. Export endpoints validated for CSV/NetCDF response headers.

