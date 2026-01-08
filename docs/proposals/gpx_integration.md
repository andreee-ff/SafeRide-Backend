# 🌟 Technical Vision: GPX Route Orchestration

## 1. Overview
Instead of treating routes as static ride properties, the SafeRide ecosystem proposes a "Template-First" approach where routes are independent assets that can be reused, shared, and monitored with precision.

## 2. Advanced Visibility & Gamification
The system supports multiple visibility modes to enhance the ride experience:
- **Public:** The full route is visible to all participants immediately.
- **Reveal on Start:** The route is kept secret until the organizer triggers the "Start" event.
- **Mystery Tour:** Participants only see the "Live Path" (where they have been) and the current location of the leader, without knowing the future destination.

## 3. Integration Roadmap

### Phase 1: Managed Import (Implemented)
- **Status:** Backend schema, async repositories, and XML validation are complete.
- **Feature:** Organizers can upload `.gpx` files. The system automatically extracts distance and elevation metadata using `gpxpy`.

### Phase 2: Platform Synchronization
- **Strava/Komoot Integration:** Direct API connections to fetch routes from popular cycling platforms, removing the need for manual file handling.

### Phase 3: "Magnet" Route Builder
- **Native Editor:** A web-based tool allowing users to click major POIs on the map. The backend will use routing engines (GraphHopper/OSRM) to "snap" these points to the best cycling infrastructure.

## 4. Technical Specifications
- **Data Integrity:** Server-side XML parsing ensures that only valid coordinate sequences are persisted.
- **Performance:** Pre-calculation of ride complexity (easy/medium/hard) allows for fast filtering on the dashboard without expensive on-the-fly math.
- **Storage Strategy:** Large GPX files are currently stored in a relational `TEXT` column but are optimized for future migration to object storage (S3).
