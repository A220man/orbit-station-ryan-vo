# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to Orbit Station will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-12

### Added
- Initial release of Orbit Station: dynamic neural network execution backend evaluation and operator coverage platform.
- Deterministic operator coverage analysis engine supporting MPS, Vulkan, CPU, and CUDA execution targets.
- Benchmark telemetry simulation and profiling suite for latency, throughput, and memory scaling.
- Workload plan evaluation and fallback execution graph resolution.
- OIDC/Keycloak authentication with role-based access control (viewer, operator, admin) and local demo mode.
- Multi-provider LLM advisory adapter support (OpenAI-compatible, Anthropic, Gemini, Ollama) with strict offline fallbacks.
- React + TypeScript dashboard with interactive operator matrix, benchmark runner, and report export.
- Complete Docker and Docker Compose environment with health checks and Keycloak SSO configuration.
