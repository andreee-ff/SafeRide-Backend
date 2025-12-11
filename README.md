# 🚴‍♂️ SafeRide API v2 - Development Branch

**📦 Backend Documentation** | [📱 Frontend README](../saferide_frontend/README.md) | [📋 Project Status](../PROJECT_STATUS.md)

---

> **⚠️ This is the active development branch (`dev/v2`).**  
> For the stable evaluation version, see the [`main` branch](https://github.com/andreee-ff/saferide_api).

A modern FastAPI-based REST API for organizing and tracking group bicycle rides in real-time with GPS coordinates, user authentication, and ride management.


## Table of Contents

- [TL;DR - Quick Start](#tldr---quick-start)
- [Development Workflow](#development-workflow)
- [What's New in v2 (Development)](#whats-new-in-v2-development)
- [v1 Status (Stable in `main`)](#v1-status-stable-in-main)
- [Features](#features)
- [Core Functionality](#core-functionality)
- [Database: PostgreSQL](#database-postgresql)
- [API Endpoints](#api-endpoints)
- [Quick Start](#quick-start)
- [Alternative Setup Options](#alternative-setup-options)
- [Test Coverage](#test-coverage)
- [Authentication](#authentication)
- [Database Management & Seeding](#database-management--seeding)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)
- [License](#license)
- [About This Project](#about-this-project)
- [Development Process](#development-process)

---

## TL;DR - Quick Start

### 🆕 First Time Setup (Fresh Installation)

```powershell
# 1. Start PostgreSQL in Docker
docker run --name saferide_postgres -e POSTGRES_USER=saferide_user -e POSTGRES_PASSWORD=yourpass -e POSTGRES_DB=saferide_db -p 5432:5432 -d postgres:16

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "DATABASE_URL=postgresql://saferide_user:yourpass@localhost:5432/saferide_db" > .env
echo "SECRET_KEY=your-secret-key-here-change-in-production" >> .env

# 5. Create database schema and seed data
python -c "from sqlalchemy import create_engine; from app.models import DbModel; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); DbModel.metadata.create_all(engine); print('✅ Database schema created!')"
python seed_data.py

# 6. Run the server
uvicorn app.main:create_app --factory --reload

# 🎉 Open http://localhost:8000/docs
# 🔐 Test credentials: vadim / 123456
```

### 🔄 Restart (Already Installed)

```powershell
# 1. Start PostgreSQL (if not running)
docker start saferide_postgres

# 2. Activate virtual environment
.\venv\Scripts\activate

# 3. Run the server
uvicorn app.main:create_app --factory --reload

# 🎉 Open http://localhost:8000/docs
```

### 🔧 Database Reset (When Schema Changes)

```powershell
# Drop and recreate all tables (⚠️ deletes all data!)
python -c "from sqlalchemy import create_engine; from app.models import DbModel; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); DbModel.metadata.drop_all(engine); DbModel.metadata.create_all(engine); print('✅ Database reset complete!')"

# Reload test data
python seed_data.py
```

[⬆️ Back to Top](#table-of-contents)

---

## Development Workflow

### Branch Strategy
- **`main`** - 📌 Stable version for ReDI School evaluation (protected)
- **`dev/v2`** - 🚀 Active development branch (YOU ARE HERE)

### Working in dev/v2

```powershell
# Daily development workflow
git checkout dev/v2
# ... make changes ...
git add .
git commit -m "feat: your feature description"
git push

# When v2 is ready for release
git checkout main
git merge dev/v2
git tag -a v2.0 -m "Version 2.0 release"
git push origin main --tags
```

[⬆️ Back to Top](#table-of-contents)

---

## What's New in v2 (Development)

### ✅ Completed
- ✅ **PostgreSQL Migration** - Production-ready database (Docker)
- ✅ **Environment Configuration** - .env file support
- ✅ **Docker Ready** - One-command PostgreSQL setup
- ✅ **Modular Architecture** - Routers and repositories split into separate files
- ✅ **Timestamps** - Auto-generated `created_at` and `updated_at` fields
- ✅ **DRY Serialization** - TimestampMixin for consistent datetime formatting
- ✅ **WebSockets** - Real-time GPS updates (Socket.IO)
- ✅ **New Ride Filters** - /rides/owned and /rides/joined endpoints

### 🚨 Security TODO (CRITICAL for Production)
> **⚠️ WARNING: Passwords are currently stored in plain text!**  
> This is acceptable for learning/development, but **MUST BE FIXED** before production.
>
> **What needs to be done:**
> - [ ] Install `passlib[bcrypt]` for password hashing
> - [ ] Add `hash_password()` and `verify_password()` to `app/security.py`
> - [ ] Update `UserRepository.create_user()` to hash passwords
> - [ ] Update `auth.login()` to use `verify_password()`
> - [ ] Re-seed database with hashed passwords
>
> **Why this is critical:**
> - Plain text passwords are visible in database dumps
> - Anyone with database access can see all passwords
> - Violates OWASP security guidelines
> - Major security vulnerability for real users
>
> **See:** [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

### 🔄 Planned Features
- 📊 **Group Analytics** - Calculate group "spread" distance
- 🗺️ **Route History** - Store complete GPS tracks
- 📱 **Mobile-ready** - Enhanced API for mobile apps
- ⚠️ **Smart Alerts** - Auto-notify when riders fall behind
- 🌤️ **Weather Integration** - Real-time weather data
- 🎨 **Heat Maps** - Visualize problem areas
- 🗺️ **PostGIS** - Advanced geospatial queries

### In Progress
- [ ] Distance calculation algorithms
- [ ] Route storage schema

[⬆️ Back to Top](#table-of-contents)

---

## v1 Status (Stable in `main`)
- ✅ 128 tests passing (Unit + Integration + Comprehensive)
- ✅ Complete CRUD operations
- ✅ JWT authentication
- ✅ GPS coordinate tracking
- ✅ Production-ready for evaluation

## Features

- ✅ User registration and authentication (JWT tokens)
- ✅ Create bicycle rides with unique join codes
- ✅ Join rides using ride code
- ✅ **Real-time GPS Tracking** via WebSockets (Socket.IO)
- ✅ Track all participants' positions in real-time
- ✅ Filter rides by "Owned by me" and "Joined by me"
- ✅ Future: Analyze group "spread" and identify stragglers and problems
- ✅ Comprehensive API documentation (Swagger UI)
- ✅ **128 comprehensive tests** (100% passing)
- ✅ **PostgreSQL database** with SQLAlchemy ORM (Docker ready)
- ✅ Pydantic data validation
- ✅ Environment-based configuration (.env)

[⬆️ Back to Top](#table-of-contents)

## Core Functionality

**1. User Registration & Authentication**
- Users register with username/password
- Login with JWT token authentication
- Identify current user via `/auth/me`

**2. Create Bicycle Rides**
- Organizer creates a ride (title, description, start time)
- System generates unique 6-character join code (e.g., `A3X9K2`)
- Share code with participants
- **View created rides:** `GET /rides/owned`

**3. Join Rides by Code**
- Participants join by entering the ride code
- Creates participation record in database
- **View joined rides:** `GET /rides/joined`

**4. Real-time GPS Tracking (WebSockets)**
- Frontend connects via Socket.IO
- Participants emit positional updates
- All participants in the same "room" (ride) receive live updates
- Fallback: `PUT /participations/{id}` for HTTP updates

### Socket.IO Protocol

**Events (Client -> Server):**
- `join_ride`: Client joins a specific ride room.
  - Payload: `{ "ride_code": "ABC123" }`
- `update_location`: Client sends new GPS coordinates.
  - Payload: `{ "ride_code": "ABC123", "user_id": 1, "latitude": 48.135, "longitude": 11.582 }`

**Events (Server -> Client):**
- `location_update`: Broadcasted to all other participants in the room.
  - Payload: `{ "user_id": 1, "latitude": 48.135, "longitude": 11.582, "location_timestamp": "2023-..." }`

**5. Group Analytics (Future Development)**
- Calculate distances between participants
- Identify riders falling behind
- Visualize group dynamics and spread

[⬆️ Back to Top](#table-of-contents)

## Database: PostgreSQL

**Database**: PostgreSQL 16 (Docker)

**Why PostgreSQL:**

**Production Ready:**
- ✅ Handles concurrent writes from multiple users
- ✅ Industry-standard relational database
- ✅ Scales to thousands of simultaneous connections
- ✅ ACID compliant with advanced transaction support

**Future-Proof:**
- ✅ **PostGIS extension** ready for advanced GPS/geospatial queries
- ✅ JSON fields for storing complete GPS tracks
- ✅ Advanced indexing for performance optimization
- ✅ Full-text search capabilities

**Development Benefits:**
- ✅ Docker containerized — one command to start
- ✅ SQLAlchemy ORM — database-agnostic code
- ✅ Can fallback to SQLite for testing (no PostgreSQL required)
- ✅ Environment-based configuration (.env file)

**Ready for v2 Features:**
- 🔄 WebSockets for real-time updates
- 📊 Complex analytics and distance calculations
- 🗺️ Route history and GPS track storage
- 🌤️ Integration with external APIs (weather, maps)

[⬆️ Back to Top](#table-of-contents)

## API Endpoints

### Users (`/users`)
- `POST /users/` - Create new user
- `GET /users/{id}` - Get user by ID
- `GET /users/` - Get all users

### Authentication (`/auth`)
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user profile

### Rides (`/rides`)
- `POST /rides/` - Create new ride
- `GET /rides/` - Get all rides
- `GET /rides/{id}` - Get ride by ID
- `GET /rides/code/{code}` - Get ride by code
- `GET /rides/owned` - Get rides created by current user
- `GET /rides/joined` - Get rides joined by current user
- `PUT /rides/{id}` - Update ride
- `DELETE /rides/{id}` - Delete ride

### Participation (`/participations`)
- `POST /participations/` - Join a ride by code
- `GET /participations/` - Get all participations
- `GET /participations/{id}` - Get participation details
- `PUT /participations/{id}` - Send GPS coordinates (HTTP fallback)
- `DELETE /participations/{id}` - Leave a ride (Cancel participation)

[⬆️ Back to Top](#table-of-contents)

## Quick Start

### Prerequisites
- Python 3.13+
- Docker Desktop (for PostgreSQL)
- pip

### Installation

**1. Clone and enter project:**
```sh
cd saferide_api
```

**2. Create virtual environment:**
```sh
# Linux/Mac
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate
```

**3. Install dependencies:**
```sh
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

**4. Start PostgreSQL (Docker):**
```powershell
docker run --name saferide_postgres `
  -e POSTGRES_USER=saferide_user `
  -e POSTGRES_PASSWORD=yourpassword `
  -e POSTGRES_DB=saferide_db `
  -p 5432:5432 `
  -d postgres:16
```

**5. Configure environment:**

Create `.env` file in project root:
```env
DATABASE_URL=postgresql://saferide_user:yourpassword@localhost:5432/saferide_db
SECRET_KEY=your-secret-key-change-this
```

**6. Initialize database:**
```powershell
# Create tables
python seed_data.py --reset

# Add demo data (user: vadim/123456, ride: ABC123)
python seed_data.py
```

### Running the Application

**Start the server:**
```powershell
# Using helper script (Windows PowerShell)
.\start-backend.ps1

# Manual start
uvicorn app.main:create_app --factory --reload
```

**Access API documentation:**
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

[⬆️ Back to Top](#table-of-contents)

---

## Alternative Setup Options

### Option 1: Use SQLite Instead of PostgreSQL

If you don't want to use Docker, you can run with SQLite:

1. **Comment out `DATABASE_URL` in `.env`:**
```env
# DATABASE_URL=postgresql://saferide_user:yourpassword@localhost:5432/saferide_db
```

2. **The app will automatically use SQLite** (`ride.db` file)

3. **Run normally:**
```powershell
python seed_data.py --reset
python seed_data.py
uvicorn app.main:create_app --factory --reload
```

### Option 2: PostgreSQL Without Docker

Install PostgreSQL natively:

1. Download from [postgresql.org/download](https://www.postgresql.org/download/)
2. Create database and user via pgAdmin
3. Update `.env` with your credentials
4. Run as usual

[⬆️ Back to Top](#table-of-contents)

---

### Testing with Postman

**Import the Postman collection:**
1. Open Postman
2. Click **Import** button
3. Select `SafeRide_API.postman_collection.json` from the project root
4. Set base URL variable: `baseUrl = http://127.0.0.1:8000`
5. Start testing endpoints with ready-made requests!

The collection includes all API endpoints organized by feature (Users, Authentication, Rides, Participations).

### Running Tests

**Note:** Tests use SQLite in-memory database (no PostgreSQL required for testing)

```sh
# Run all 128 tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=html
```

## Test Coverage

**Total: 128 tests (100% passing)** ✅

| Category | Tests | Status |
|----------|-------|--------|
| Unit Tests (auth, rides) | ~60 | ✅ PASS |
| Integration Tests (flows) | ~40 | ✅ PASS |
| Comprehensive (Edge cases) | ~28 | ✅ PASS |
| **Total** | **128** | **✅ PASS** |

### Test Categories
- Authentication & Authorization
- Ride Management (Create, Join, Leave, Edit)
- **New:** Owned & Joined Ride Filtering
- Participation Management
- **New:** WebSocket Connection & Event Handling
- Data Validation
- Edge Cases
- Security & JWT handling
- Concurrency

**See `TESTING.md` for detailed test instructions.**

## Authentication

The API uses JWT (JSON Web Token) authentication.

**How to authenticate:**
1. Create a user: `POST /users/` with username and password
2. Login: `POST /auth/login` with credentials (returns JWT token)
3. Use token: Add `Authorization: Bearer {token}` header to protected endpoints

### Windows PowerShell Usage (Primary Example)

Demo user: `vadim` / `123456` (created by `seed_data.py`).

PowerShell does NOT treat single quotes inside JSON like bash. Escape inner double quotes or build JSON via `ConvertTo-Json`. Always invoke `curl.exe` (native binary) rather than the `curl` alias (which maps to `Invoke-WebRequest`).

#### Step 1: Create user (idempotent)
```powershell
curl.exe -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d "{\"username\":\"vadim\",\"password\":\"123456\"}"
```
If the user already exists you will get `409 Conflict`.

Readable alternative:
```powershell
$body = @{ username = "vadim"; password = "123456" } | ConvertTo-Json
curl.exe -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d $body
```

#### Step 2: Login and get token
```powershell
$login = curl.exe -X POST "http://127.0.0.1:8000/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=vadim&password=123456"
$token = ($login | ConvertFrom-Json).access_token
Write-Host "Token: $token"
```

#### Step 3: Authenticated request
```powershell
curl.exe -X GET "http://127.0.0.1:8000/auth/me" -H "Authorization: Bearer $token"
```

#### One-line quick workflow
```powershell
curl.exe -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d "{\"username\":\"vadim\",\"password\":\"123456\"}"; $login = curl.exe -X POST "http://127.0.0.1:8000/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=vadim&password=123456"; $token = ($login | ConvertFrom-Json).access_token; curl.exe -X GET "http://127.0.0.1:8000/auth/me" -H "Authorization: Bearer $token"
```

#### Common PowerShell pitfalls
- Using `curl` alias instead of `curl.exe` → headers lost / wrong behavior
- Not escaping quotes inside JSON → 422 JSON decode error
- Trailing spaces after backticks in multiline → malformed body
- Single quotes around JSON keys/values → invalid JSON for this API

### POSIX (Linux / macOS) Example

#### Step 1: Create a User
```bash
curl -X POST "http://127.0.0.1:8000/users/" \
	-H "Content-Type: application/json" \
	-d '{"username": "vadim", "password": "123456"}'
```

**Response:**
```json
{
	"id": 1,
	"username": "vadim"
}
```

#### Step 2: Login and Get Token
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
	-H "Content-Type: application/x-www-form-urlencoded" \
	-d "username=vadim&password=123456"
```

**Response:**
```json
{
	"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
	"token_type": "bearer"
}
```

**Copy the `access_token` value** - you'll use it in the next step.

#### Step 3: Use Token to Access Protected Endpoints
Replace `{your_token_here}` with the token from Step 2:

```bash
curl -X GET "http://127.0.0.1:8000/auth/me" \
	-H "Authorization: Bearer {your_token_here}"
```

**Response:**
```json
{
	"id": 1,
	"username": "vadim"
}
```

### Using Swagger UI (Recommended for Testing)

The easiest way to test the API is using Swagger UI:

1. **Start the server:**
	 ```sh
	 uvicorn app.main:create_app --factory --reload
	 ```

2. **Open Swagger UI:**
	 ```
	 http://127.0.0.1:8000/docs
	 ```

3. **Test endpoints directly in browser:**
	 - Create a user: Click "POST /users/" → "Try it out"
	 - Login: Click "POST /auth/login" → "Try it out"
	 - Get token automatically stored by Swagger
	 - Test other endpoints with automatic auth

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Missing or invalid token | Check token is correct and not expired |
| `422 Unprocessable Content` | Invalid request format | Check JSON format and required fields |
| `409 Conflict` | Username already exists | Use different username |
| `404 Not Found` | Endpoint doesn't exist | Check endpoint URL spelling |

## Database Management & Seeding

The app uses **PostgreSQL** database (via Docker).

### 🐳 Docker Commands

**Start PostgreSQL:**
```powershell
docker start saferide_postgres
```

**Stop PostgreSQL:**
```powershell
docker stop saferide_postgres
```

**View logs:**
```powershell
docker logs saferide_postgres
```

**Remove container (data will be lost!):**
```powershell
docker rm -f saferide_postgres
```

### 🗄️ Database Access

**Connect via psql (interactive):**
```powershell
docker exec -it saferide_postgres psql -U saferide_user -d saferide_db
```

Inside psql:
```sql
\dt                    -- List all tables
\d users              -- Describe users table
SELECT * FROM users;  -- Query data
\q                    -- Quit
```

**Run SQL query directly:**
```powershell
docker exec -it saferide_postgres psql -U saferide_user -d saferide_db -c "SELECT * FROM users;"
```

### 🌱 Seeding Data

**Reset Database:**
Remove all tables and recreate empty schema:
```sh
python seed_data.py --reset
```

**Seed Default Demo Data:**
Creates demo users, rides, and participation records:
```sh
python seed_data.py
```
Creates:
- User: `vadim` / password: `123456`
- Demo ride: `ABC123`
- Sample participation records

Script is idempotent (won't create duplicates).

**Seed Large Dataset:**
Generate random test data:
```sh
python seed_data.py --massive
```
Creates:
- Fixed user: `vadim` / `123456`
- Random users
- Random rides
- Random participation entries

### Custom Data Volume
```sh
python seed_data.py --massive --users=50 --rides=100 --participations=500
```

## Environment Variables

Configuration via `.env` file (optional, has safe defaults):

```env
# JWT Configuration
SECRET_KEY="dev-secret-key-change-me"  # Change for production!
ALGORITHM="HS256"                       # Token algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=60          # Token expiration time
```

**For Production:**
```bash
export SECRET_KEY="your-secure-random-key"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Project Structure

```
saferide_api/
├── app/                          # Core application
│   ├── main.py                  # FastAPI app factory with routes
│   ├── models.py                # SQLAlchemy ORM models (User, Ride, Participation with GPS)
│   ├── schemas.py               # Pydantic validation schemas
│   ├── routers.py               # API endpoint definitions
│   ├── repositories.py          # Data access layer (ride code generation, GPS updates)
│   ├── security.py              # JWT token management
│   ├── injections.py            # Dependency injection
│   └── __init__.py
│
├── tests/                        # Original test suite (24 tests)
│   ├── test_auth_login.py       # Authentication tests
│   ├── test_auth_register.py    # User registration tests
│   ├── test_operate_with_ride.py # Ride management tests
│   ├── test_participations.py   # Participation + GPS tests
│   ├── test_unit_auth_and_ride.py # Unit tests
│   └── conftest.py              # Pytest fixtures
│
├── AI_Assistant_Analysis/        # AI-generated materials
│   ├── README_AI.md             # Test analysis overview
│   ├── TEST_COMPARISON_EN.md    # Test comparison (English)
│   ├── TEST_ENHANCEMENT_ROADMAP.md # Future improvements
│   └── comprehensive_tests/     # 26 comprehensive tests
│
├── .env                         # Environment variables
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── seed_data.py                 # Database seeding script
├── SafeRide_API.postman_collection.json  # Postman API collection
└── README.md                    # This file
```

[⬆️ Back to Top](#table-of-contents)

## Development

### Technology Stack
- **FastAPI** - Modern Python web framework
- **PostgreSQL 16** - Production-grade database
- **SQLAlchemy** - Database ORM (supports both PostgreSQL & SQLite)
- **psycopg2** - PostgreSQL driver
- **Docker** - Containerized PostgreSQL
- **Pydantic** - Data validation and schemas
- **pytest** - Testing framework
- **python-dotenv** - Environment configuration
- **JWT** - Authentication tokens

### Code Style
- Type hints throughout
- Pydantic for data validation
- SQLAlchemy ORM for database abstraction
- FastAPI dependency injection
- Environment-based configuration
- TDD approach - Tests first, then code

### Adding New Tests
Tests should go in `/tests` for original tests or `AI_Assistant_Analysis/comprehensive_tests/` for additional integration tests.

Running tests:
```sh
pytest tests/ -v
```

## Troubleshooting

**Virtual environment not activating?**
- Windows: Use `.\venv\Scripts\Activate.ps1` (PowerShell)
- Mac/Linux: Use `source venv/bin/activate`

**Database locked error?**
- Delete `*.db` files and restart
- Run `python seed_data.py` to reseed

**Port 8000 already in use?**
```sh
uvicorn app.main:create_app --factory --port=8001 --reload
```

**Tests failing?**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version: 3.13+ required
- Clear cache: `pytest --cache-clear`

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)

## License

Maybe ... one day ;)

## About This Project

This project was created as a final project after completing the Python Backend Development course at **ReDI School of Digital Integration Munich**.

## Development Process

**Developer: Vadim Andreev**
- All code logic, API design, and implementation decisions
- Core test suite in `/tests` directory (24 tests)

**AI Assistance: Claude**
- README.md documentation structure and formatting
- Comprehensive test suite in `/AI_Assistant_Analysis/comprehensive_tests` (26 additional tests)
- Code review and analysis

**Note**: The comprehensive AI-generated tests passed successfully without any modifications to the existing codebase, validating the quality of the original implementation.

---

**Last Updated:** December 09, 2025  
**Status:** Active Development (Frontend Integration Complete) ✅