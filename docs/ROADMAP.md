# 🗺️ SafeRide Backend - Strategic Roadmap

**Current Version:** v2.5 (Professional Refinement)  
**Status:** MVP Reached | Security Hardening Active

This roadmap outlines the technical and strategic direction of the SafeRide Backend, prioritizing safety, data integrity, and high-concurrency performance.

---

## 🛑 Phase 1: Security & Stability (Completed / Verified)
*Focus on industry-standard core safety.*

- [x] **🔒 Robust Password Hashing**
    - Transitioned from plain-text storage to **Argon2 / Bcrypt** via `pwdlib`.
- [x] **🛡️ Performance Verification**
    - Achieved 100% pass rate on a comprehensive 138-test suite (Unit, Integration, Concurrency).
- [x] **🔐 Modern Async Engine**
    - Fully migrated the database layer to **Async SQLAlchemy 2.0** for non-blocking operations.

---

## 🎨 Phase 2: Functional Expansion (Active)
*Enhancing the ride experience for organizers and participants.*

- [x] **📍 Technical Route Support (GPX)**
    - Implemented database schema and repositories for GPX storage and metadata extraction (distance, elevation).
- [ ] **📡 Advanced Geolocation (Hybrid)**
    - Integrate Google's **Geolocation API** as a server-side fallback for weak GPS signals (urban environments).
- [ ] **⚡ Quick Join Protocol**
    - Allow temporary guest sessions for users entering via invitation code without full registration.
- [ ] **🔄 Ride Lifecycle Management**
    - Implement rigorous state machine transitions: `Planned` -> `In Progress` -> `Finished`.

---

## 🆘 Phase 3: Crisis Management & Reliability (Upcoming)
*Safety features for emergency scenarios.*

- [ ] **🚑 Emergency Response Integration**
    - Research and implement automated alert protocols for severe anomalies.
- [ ] **👑 Leader Redundancy**
    - Mechanism to auto-assign a co-organizer if the primary lead disconnects during a session.
- [ ] **📡 Offline Resilience (Mesh)**
    - Explore BLE (Bluetooth Low Energy) for participant proximity detection when cellular data is unavailable.

---

## 🛠️ Technical Backlog
- [ ] **CI/CD Integration:** Automated testing pipelines via GitHub Actions.
- [ ] **Postman Docs:** Auto-generate API documentation from schemas.
- [ ] **Redis Backend:** Use Redis for distributed Socket.IO rooms to support horizontal scaling across multiple containers.
