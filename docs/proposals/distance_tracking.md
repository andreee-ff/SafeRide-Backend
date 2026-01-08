# 📏 Technical Concept: Proximity & Distance Tracking

## 1. Objective
To enhance safety and group coordination by providing real-time distance metrics between participants. This allows organizers and riders to identify individuals who may have fallen behind or deviated from the group.

## 2. Tracking Modalities

### A. Dynamic Proximity (Haversine Mode)
- **Use Case:** Flexible rides, group exploration, or urban environments with high connectivity.
- **Logic:** Calculate the direct straight-line distance between the current user's coordinates and other group members using the Haversine formula.
- **Implementation:**
    - **Pros:** Computationally inexpensive; no external API dependencies; works with any sporadic coordinate pair.
    - **Cons:** Does not account for road geography or navigational barriers.

### B. Track-Relative Distance (GPX Mode)
- **Use Case:** Organized rides following a predefined GPX tour.
- **Logic:** 
    - "Snap" participant coordinates to the nearest point on the active GPX polyline.
    - Calculate the distance *along the route segments* between two participants.
- **Implementation Strategy:**
    - To avoid high API costs (e.g., Google Distance Matrix), calculate offsets client-side by comparing participant indices along the simplified route geometry.
    - Alternatively, implement server-side caching of route segment distances for fast lookups.

## 3. User Interface Integration
- **Participant List:** Add a contextual badge to each participant: `📍 1.2 km away`.
- **Safety Visuals:** Automatically highlight markers and list entries in **Amber** or **Red** if a participant exceeds a pre-defined group safety radius (e.g., > 1.5 km).

## 4. Hardware/Battery Considerations
- Continuous proximity calculation should be throttled (e.g., once every 30-60 seconds) to minimize battery drain on participant devices while maintaining operational awareness.
