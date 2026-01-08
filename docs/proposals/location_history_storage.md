# 🗄️ Architectural Proposal: High-Fidelity Location History

## 1. The Challenge
Currently, the system persists only the "Most Recent" coordinate for each participant. To enable post-ride analysis (Route Replay) and accurate progress tracking, a dedicated time-series storage strategy is required.

## 2. Proposed Implementation: The Time-Series Table
We recommend a dedicated `LocationHistory` table to decouple current state from historical logs.

### Schema Definition
```sql
CREATE TABLE location_history (
    id SERIAL PRIMARY KEY,
    participation_id INTEGER REFERENCES participations(id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    speed FLOAT,
    altitude FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE
);
```

### Why a Separate Table?
- **Efficiency:** The `Participations` table remains lean, ensuring that "Current State" queries (the most frequent operation) are extremely fast.
- **Analytics:** Enables standard SQL aggregate queries (`AVG(speed)`, `SUM(distance)`) without parsing JSON or BLOBs.
- **Retention Management:** Allows for easy implementation of data expiration policies (e.g., "Delete detailed logs 48 hours after ride completion" for GDPR compliance).

## 3. Operational Strategy: Denormalization
To maintain high performance on the Live Map, we will continue to update the `latitude` and `longitude` columns in the `Participations` table in tandem with the history log. 

**Update Flow:**
1. Incoming Socket Event (`update_location`).
2. **Step A:** `UPDATE participations` (Fast overwrite for live view).
3. **Step B:** `INSERT INTO location_history` (Asynchronous append for the audit trail).

## 4. Future Potential
Storing full history allows for the introduction of "Ghost Riders" — playing back historical data from previous rides for comparison or training.
