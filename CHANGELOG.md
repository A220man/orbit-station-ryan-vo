# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 - 2026-10-21

### Added
- Comprehensive export endpoints for operators, benchmarks, and workload plans (JSON/CSV).
- End-to-end integration test covering full operator→plan→benchmark→advisory workflow.
- LLM advisory provider tests for OpenAI-compatible, Anthropic, and Gemini with mocked responses.
- Provider error handling test for graceful fallback on LLM service failures.
- Updated version references to 1.1.0 across backend, frontend, and documentation.

### Changed
- Backend test count increased from 17 to 31 tests.
- Portfolio summary updated to reflect implemented capabilities.

## 1.0.0 - 2026-10-12

### Added
- Initial release of Orbit Station: dynamic neural network execution backend evaluation and operator coverage platform.
- Deterministic operator coverage analysis engine supporting MPS, Vulkan, CPU, and CUDA execution targets.
- Benchmark telemetry simulation and profiling suite for latency, throughput, and memory scaling.
- Workload plan evaluation and fallback execution graph resolution.
- OIDC/Keycloak authentication with role-based access control (viewer, operator, admin) and local demo mode.
- Multi-provider LLM advisory adapter support (OpenAI-compatible, Anthropic, Gemini, Ollama) with strict offline fallbacks.
- React + TypeScript dashboard with interactive operator matrix, benchmark runner, and report export.
- Complete Docker and Docker Compose environment with health checks and Keycloak SSO configuration.


The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
