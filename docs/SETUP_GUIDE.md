# 🛠 SafeRide Backend - Setup Guide

This guide provides step-by-step instructions for deploying and configuring the SafeRide backend service in a standalone environment.

## 📋 Table of Contents
1. [Core Requirements](#requirements)
2. [Automated Deployment (Docker)](#automated-deployment-docker)
3. [Manual Installation (Local Core)](#manual-installation-local-core)
4. [Environment Configuration](#environment-configuration)
5. [Data Management & Seeding](#data-management--seeding)

---

## Requirements

### Runtime Environment
- **Python:** 3.12+ (AsyncIO features required)
- **Database:** PostgreSQL 15+ (Production) or SQLite (Evaluation/Dev)
- **Containerization:** Docker & Docker Compose (Recommended)

---

## Automated Deployment (Docker)

The fastest way to spin up the backend along with its PostgreSQL database.

1. **Build and Start:**
   ```bash
   docker-compose up --build -d
   ```
2. **Access API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Manual Installation (Local Core)

Recommended for deep debugging and local development.

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/macOS
```

### 2. Dependency Installation
```bash
pip install -r requirements.txt
```

### 3. Database Initialization
If you are not using Docker, ensure the `DATABASE_URL` in `.env` points to a valid instance.
```bash
# Create schema manually (if not using Alembic)
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. Running the Application
```bash
uvicorn app.main:app --reload
```

---

## Environment Configuration

Configuration is managed via the `.env` file. A template is provided in `.env.example`.

| Variable | Requirement | Description |
|----------|-------------|-------------|
| `DATABASE_URL` | Required | Connection string (Postgres/SQLite) |
| `SECRET_KEY` | Required | Key for JWT signing (use `secrets.token_hex(32)`) |

---

## Data Management & Seeding

The project includes a robust seeding script to populate the database for demonstration purposes.

### Using the Seeder

**Standard Seed (User `vadim` and demo rides):**
```bash
python seed_data.py
```

**Massive Seed (Load testing):**
```bash
python seed_data.py --massive --users=50 --rides=20
```

**Database Reset (Wipe all data):**
```bash
python seed_data.py --reset
```

> [!CAUTION]
> The `--reset` flag will permanently delete all records in the database. Use only in development environments.

---

## Troubleshooting

- **CORS Errors:** Update `ALLOWED_ORIGINS` in `app/main.py` to match your frontend URL.
- **DB Connection Failures:** Ensure PostgreSQL is running on the specified port. For Docker, use the service name `db` instead of `localhost`.
- **Hashing Errors:** Ensure `bcrypt` and `pwdlib` are correctly installed. Newer versions of `bcrypt` resolve the 72-byte limit issue.
