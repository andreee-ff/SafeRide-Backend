# 🗺️ Product Concept: Map Observation Modes

## 1. Objective
To provide a specialized map interface that adapts to the user's current role—whether they are navigating themselves or monitoring the entire group.

## 2. Strategic View Modes

### A. Team Overview (Group Dynamics)
- **Primary Goal:** Group cohesion and safety.
- **Behavior:**
    - The map automatically centers on the group's "Center of Mass."
    - Dynamic zoom adjustment (`fitBounds`) ensures every participant is visible on screen.
    - **UX:** Ideal for organizers and sweepers.

### B. Navigation Focus (Tethered View)
- **Primary Goal:** Personal guidance.
- **Behavior:**
    - The map strictly centers on the current user's location (Tethered).
    - High-detail zoom (Level 17+) is locked for optimal road visibility.
    - Other participants are allowed to move off-screen, preventing the "jitter" or zooming out caused by group spread.

## 3. Implementation Details
- **Toggle Mechanism:** Floating UI controls on the map (`🎯 Focus` vs `👥 Group`).
- **State Management:** A simple `viewMode` state variable in the map component to switch between `fitBounds` (Group) and `setCenter` (Focus) logic during coordinate updates.
- **Smart Follow Logic:** In 'Focus' mode, the map only centers when the user moves beyond a "dead zone" (15% from the center) to avoid constant micro-shaking.
