# SafeRide API - Testing Guide

## Test Structure

- `tests/` - Core Functional & Unit tests
- `AI_Assistant_Analysis/integration_tests/` - End-to-end Integration tests
- `AI_Assistant_Analysis/comprehensive_tests/` - Edge cases and System tests
- `AI_Assistant_Analysis/pending_tests/` - New feature validation tests

**Total:** 128 tests (100% passing)

## Test Types

### 1. Standard Tests (SQLite)
Fast tests that work without external dependencies. This is the default mode.
```bash
pytest
# Result: 95 passed, 2 deselected
```

### 2. PostgreSQL Tests
Tests that require PostgreSQL (CASCADE DELETE, UNIQUE constraints):

**Step 1:** Start PostgreSQL
```bash
docker start saferide_postgres

# Or create new container:
docker run --name saferide_postgres \
  -e POSTGRES_USER=saferide_user \
  -e POSTGRES_PASSWORD=MyPass2025vadim \
  -e POSTGRES_DB=saferide_db \
  -p 5432:5432 -d postgres:16
```

**Step 2:** Run PostgreSQL tests
```bash
pytest -m postgres -v
# Result: 2 passed, 95 deselected
```

## Running Tests

```bash
# Unit tests only (fast)
pytest tests/

# Integration tests only
pytest AI_Assistant_Analysis/integration_tests/

# Comprehensive tests only
pytest AI_Assistant_Analysis/comprehensive_tests/

# All tests (excluding PostgreSQL)
pytest

# PostgreSQL tests only
pytest -m postgres

# All tests including PostgreSQL
pytest AI_Assistant_Analysis/ tests/
```

## Pytest Markers

- `@pytest.mark.postgres` - tests requiring PostgreSQL database

## PostgreSQL Tests

1. **test_delete_ride_with_participations** - Verifies CASCADE DELETE  
   When a ride is deleted, all related participations are automatically deleted

2. **test_duplicate_participation_same_user** - Verifies UNIQUE constraint  
   User cannot join the same ride twice (409 CONFLICT)

## Configuration

**pytest.ini:**
```ini
[pytest]
markers =
    postgres: tests that require PostgreSQL database

addopts = -m "not postgres"  # Skip PostgreSQL tests by default
```

## Examples

```bash
# SQLite tests only (fast, default)
pytest

# PostgreSQL tests only
pytest -m postgres

# All tests (SQLite + PostgreSQL)
pytest AI_Assistant_Analysis/ tests/

# Specific PostgreSQL test
pytest -m postgres -k test_duplicate_participation_same_user -v

# Verbose output
pytest -v --tb=short
```
