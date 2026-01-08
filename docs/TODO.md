# 📋 Current Sprint - Active Development

This file tracks immediate, actionable tasks for the SafeRide backend service.

---

## 🏃 Priority Initiatives

### 🔐 Security Hardening (Highest Priority)
- [x] **Argon2 Migration**: Replace plain-text password storage with `pwdlib`.
- [x] **Test Verification**: Fix all 138 regressions following the security update.

### 📦 Standalone Migration
- [x] **Docker Isolation**: Create a standalone `docker-compose.yml` for the backend repository.
- [x] **Documentation Polish**: Translate all technical guides to professional English for the repository split.

---

## 🛠️ Backend Task Backlog

### 🗺️ GPS & Geolocation
- [ ] **Distance Calculation**: Implement backend algorithms to calculate straight-line and route-based distances between participants.
- [ ] **Location History Storage**: Design and implement a time-series schema to persist full coordinate logs for post-ride replay.

### ⚙️ Core Logic
- [x] **Async Refactoring**: (Completed) Moved core engine to FastAPI + SQLAlchemy Async.
- [ ] **Alembic Migrations**: Verify all schema versions against the live PostgreSQL container.
- [ ] **Auto-Cleanup**: Implement a background task to archive rides older than 24 hours.

### 🧪 Quality Assurance
- [ ] **Load Testing**: Stress-test the Socket.IO broadcasting loop with 100+ simulated concurrent updates.
- [ ] **Test Consolidation**: Merge temporary AI-generated tests into the main `tests/` directory.
