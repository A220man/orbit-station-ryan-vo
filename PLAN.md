# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

backend-core-engine

## Roadmap

### foundation-and-metadata — Project scaffolding, packaging, and CI configuration

Status: done

Acceptance:
- Repository includes portfolio.json, pyproject.toml, LICENSE, README, .gitignore, compose.yaml, and CI workflows.
- Preflight validation recognises project layout and metadata.

Implementation: `portfolio.json`, `pyproject.toml`, `compose.yaml`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_config.py`

### backend-core-engine — Substantive ML execution and operator coverage engine with SQLite persistence

Status: done

Acceptance:
- FastAPI backend with models, database repository, and deterministic operator analysis engine.
- Supports MPS, Vulkan, CPU, and CUDA operator catalog with capability querying and fallback resolution.
- Workload execution planner and telemetry benchmark simulation.
- At least 12 comprehensive unit and integration tests passing.

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/models/database.py`, `backend/app/services/operator_catalog.py`, `backend/app/services/benchmark_engine.py`, `backend/app/services/workload_planner.py`, `backend/app/services/llm_advisory.py`, `backend/app/api/endpoints.py`

Tests: `backend/tests/test_api.py`, `backend/tests/test_engine.py`, `backend/tests/test_auth.py`

### frontend-dashboard — React + TypeScript dashboard for operator coverage and benchmark simulation

Status: done

Acceptance:
- Vite + React SPA with typed API client, responsive layout, and distinct domain components.
- Interactive coverage matrix, workload planner runner, and exportable reports.
- Typecheck and tests pass cleanly.

Implementation: `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/components/CoverageMatrix.tsx`, `frontend/src/components/BenchmarkRunner.tsx`, `frontend/src/components/WorkloadPlannerView.tsx`

Tests: `frontend/src/App.test.tsx`

