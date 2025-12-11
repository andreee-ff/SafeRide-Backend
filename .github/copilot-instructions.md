# Ride App - AI Coding Agent Guidelines

## Project Overview
A FastAPI-based ride-sharing API with SQLAlchemy ORM, JWT authentication, and location tracking. Three main entities: Users, Rides (organized by users), and Participations (users joining rides with coordinates).

## Architecture & Data Flow

### Core Components
- **`app/main.py`**: Factory-pattern app with lifespan manager (SQLite setup/teardown)
- **`app/models.py`**: SQLAlchemy ORM models (UserModel, RideModel, ParticipationModel)
- **`app/schemas.py`**: Pydantic schemas for request/response validation with custom datetime serialization (UTC +00:00 format)
- **`app/repositories.py`**: Data access layer with query methods and business logic
- **`app/routers.py`**: FastAPI route handlers organized by feature (users, auth, rides, participations)
- **`app/injections.py`**: Dependency injection for repositories and session management
- **`app/security.py`**: JWT token creation/verification with environment-based configuration

### Data Model Relationships
```
UserModel (1) ──── organized_rides ──── (N) RideModel
            ├──── participated_in_rides ──── ParticipationModel
RideModel (1) ──── has_participants ──── (N) ParticipationModel
```

**Key Fields:**
- Rides: Auto-generate unique 6-char code (uppercase + digits), UTC timestamps
- Participations: Store lat/long as Numeric(10,8), track updated_at per location update
- All datetime fields: timezone-aware, stored UTC

### Authorization Pattern
- **User routes**: Public registration and lookup
- **Auth routes**: `/auth/login` (OAuth2PasswordRequestForm), `/auth/me` (requires token)
- **Ride routes**: Create/update requires authentication; delete/update requires ownership
- **Participation routes**: Create/update requires authentication; update requires ownership
- **Token extraction**: `get_current_user()` returns Pydantic schema; `get_current_user_model()` returns ORM model

## Critical Conventions

### Repository Methods
- Use SQLAlchemy 2.0 patterns: `select()` statements, `scalar_one_or_none()`, `scalars().all()`
- **Naming**: `get_*()` queries, `create_*()` inserts, `update_*()` patches, `delete_*()` removes
- Mix of `.query()` (legacy) and `.execute(select(...))` (modern) - standardize to modern on refactors
- **No commits in repository**: Use `.flush()` only; session manages transactions via dependency injection

### Datetime Handling
- **Database**: Store all datetimes as `DateTime(timezone=True)` (server default: `func.now()`)
- **Schemas**: Use custom `@field_serializer` to convert to UTC ISO format with `+00:00` suffix (not `Z`)
- **Input**: Accept timezone-aware datetimes; tests use `datetime(..., tzinfo=timezone.utc)`

### Error Responses
- Use `HTTPException` with `status_code` and optional `detail` message
- Common patterns: `404 NOT_FOUND`, `401 UNAUTHORIZED`, `403 FORBIDDEN`, `409 CONFLICT`, `422 UNPROCESSABLE_CONTENT`
- Duplicate username/user creation errors: Return `409 CONFLICT`, catch generic exceptions

### Dependency Injection
- All route handlers use `Annotated[Type, Depends(injection_function)]` pattern
- Session is per-request, auto-rolled-back on exceptions (see `conftest.py` override)
- Repositories are lightweight wrappers around session; instantiated per request

## Testing Patterns

### Test Structure
- **`conftest.py`**: Fixtures for app, session (in-memory SQLite), test_client, test users, ride factory
- **Fixture scope**: `function` scope to isolate tests
- **Session management**: Override `get_session` dependency to inject test session; auto-rollback and drop tables after
- **Factory pattern**: `ride_factory` fixture generates test rides with random codes

### Test Conventions
- Use `TestClient` from fastapi for route testing
- Setup test data in fixtures; tear down automatic via `finally: DbModel.metadata.drop_all()`
- Auth tests: Create user, login, extract token, pass in headers
- Assert with `response.status_code` and `response.json()` for validation

## Running the App

```sh
# Dev server (auto-reload, SQLite default)
uvicorn app.main:create_app --factory --reload

# Tests (pytest, auto-discovers tests/)
pytest

# View current JWT via /auth/me (requires Authorization header)
```

## Environment Variables
- `SECRET_KEY`: JWT signing key (default: "dev-secret-key-change-me")
- `ALGORITHM`: JWT algorithm (default: "HS256")
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime in minutes (default: 60)

## Common Tasks

**Add a new route:**
1. Define schema in `schemas.py` (inherit from Base as needed)
2. Add repository method in `repositories.py` (use `.execute(select(...))` pattern)
3. Define route in `routers.py` with `Depends()` injection, auth check if needed
4. Test in `tests/test_*.py` using conftest fixtures

**Update ride participation fields:**
- Modify `ParticipationModel` in `models.py`
- Update schemas in `schemas.py` and serializers
- Repository handles nullable/optional fields via `setattr()` in `update_*()` methods

**Fix timestamp issues:**
- Ensure all datetime fields use `DateTime(timezone=True)`
- Schemas must have custom serializers returning ISO format with `+00:00`
- Tests: Always use `datetime(..., tzinfo=timezone.utc)`
