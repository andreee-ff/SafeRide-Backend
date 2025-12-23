from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
import subprocess
import os
import sys
import asyncio
import random
import datetime

from app.schemas import SimulationStart, SimulationAnimate

from app.injections import (
    get_ride_repository,
    get_participation_repository,
)
from app.repositories import (
    RideRepository,
    ParticipationRepository,
)

router = APIRouter()

async def animate_task(ride_code: str, initial_movers: list[dict]):
    """
    Background task to animate existing participants.
    Operates purely on in-memory data, no DB access.
    """
    from app.sockets import sio
    
    movers = initial_movers
    
    print(f"DEBUG: Animating {len(movers)} participants for ride {ride_code}")

    # Animation Loop (60 seconds)
    try:
        for _ in range(60):
            for m in movers:
                m["lat"] += m["d_lat"] + random.uniform(-0.00005, 0.00005)
                m["lon"] += m["d_lon"] + random.uniform(-0.00005, 0.00005)
                
                # Bounce
                base_lat = 48.1351
                base_lon = 11.5820
                if abs(m["lat"] - base_lat) > 0.05: m["d_lat"] *= -1
                if abs(m["lon"] - base_lon) > 0.05: m["d_lon"] *= -1
                
                payload = {
                    "ride_code": ride_code,
                    "user_id": m["user_id"],
                    "latitude": m["lat"],
                    "longitude": m["lon"],
                    "location_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                # Fix: Emit 'location_update' (what client listens to) to the specific room
                await sio.emit("location_update", payload, room=ride_code)
                
            await asyncio.sleep(1)
    except Exception as e:
        print(f"CRITICAL ERROR in animate_task: {e}")

@router.post("/animate")
async def animate_participants(
    data: SimulationAnimate, 
    ride_repository: Annotated[RideRepository, Depends(get_ride_repository)],
    participation_repository: Annotated[ParticipationRepository, Depends(get_participation_repository)]
):
    """
    Animates ALL participants currently in the ride DB.
    """
    # Fetch by ID as requested
    ride = await ride_repository.get_by_id(ride_id=data.ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    parts = await participation_repository.get_by_ride_id(ride_id=ride.id)
    
    # Prepare data for background task (detach from DB session)
    base_lat = 48.1351
    base_lon = 11.5820
    
    movers = []
    for p in parts:
        lat = float(p.latitude) if p.latitude else base_lat + random.uniform(-0.01, 0.01)
        lon = float(p.longitude) if p.longitude else base_lon + random.uniform(-0.01, 0.01)
        movers.append({
            "user_id": p.user_id,
            "lat": lat,
            "lon": lon,
            "d_lat": random.uniform(-0.0002, 0.0002),
            "d_lon": random.uniform(-0.0002, 0.0002)
        })

    # Start background task with SAFE data
    if movers:
        asyncio.create_task(animate_task(ride.code, movers))
        
    return {"message": "Animation started for existing participants"}

@router.post("/start")
async def start_simulation(data: SimulationStart):
    """
    Launches the ghost_rider.py script in a subprocess.
    """
    try:
        # Resolve path to ghost_rider.py
        # Assuming we are in backend/app/routers/simulation.py
        # Script is in backend/tests/debug_tools/ghost_rider.py
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_path = os.path.join(base_dir, "tests", "debug_tools", "ghost_rider.py")
        
        if not os.path.exists(script_path):
             # Fallback for different CWD
             script_path = os.path.join("tests", "debug_tools", "ghost_rider.py")

        # Python executable
        python_exe = sys.executable

        # Command: python ghost_rider.py [user] [pass] [code] [count]
        cmd = [
            python_exe,
            script_path,
            data.username_base,
            "swarmpass", # Default password for simulation
            data.ride_code,
            str(data.count)
        ]

        # Launch in background (independent process)
        kwargs = {}
        if os.name == 'nt':
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        
        subprocess.Popen(cmd, **kwargs)

        return {"message": f"Simulation started with {data.count} bots", "command": " ".join(cmd)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")
