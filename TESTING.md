# 🧪 SafeRide API - Testing Guide

## Test Architecture

The testing strategy covers functional units, integration points, and high-concurrency scenarios to ensure system reliability.

- `tests/` — Core Functional and Unit tests.
- `AI_Assistant_Analysis/integration_tests/` — End-to-end integration flows.
- `AI_Assistant_Analysis/comprehensive_tests/` — Edge cases and system-level validation.
- `AI_Assistant_Analysis/pending_tests/` — Regression and new feature validation.

**Current Status:** 138 tests (100% passing).

## Execution Modes

### 1. Standard Suite (SQLite)
Fast, in-memory testing without external dependencies. This is the recommended mode for local development.
```bash
pytest
```

### 2. High-Fidelity Suite (PostgreSQL)
Specific tests that validate database-level features like `CASCADE DELETE` and `UNIQUE` constraints.

**Step 1: Start PostgreSQL (Docker)**
```bash
docker-compose up -d db
```

**Step 2: Run PostgreSQL-tagged tests**
```bash
pytest -m postgres -v
```

## Advanced Usage

### Target Specific Domains
```bash
# Core logic only
pytest tests/

# Integration flows only
pytest AI_Assistant_Analysis/integration_tests/

# Comprehensive system checks
pytest AI_Assistant_Analysis/comprehensive_tests/
```

### Filtering and Markers
- `@pytest.mark.postgres`: Identifies tests requiring a live PostgreSQL instance.
- **Default Behavior:** PostgreSQL tests are skipped by default to ensure speed (configured in `pytest.ini`).

## Key Test Scenarios
1. **Cascade Verification**: Ensures that deleting a ride automatically removes all associated participant records.
2. **Concurrency Safety**: Validates that users cannot join the same ride multiple times simultaneously.
3. **Security Audit**: Verifies that protected endpoints strictly require valid JWT tokens and that password hashing is enforced.

## Troubleshooting
For detailed logs during test execution:
```bash
pytest -v --tb=short
```
