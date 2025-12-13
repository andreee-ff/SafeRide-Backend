import asyncio
import socketio
import aiohttp
import sys
import random

# Ghost Rider: Simulates moving users on a ride
# ------------------------------------------------------------------------------
# Usage:
#   python ghost_rider.py [username_base] [password] [ride_code] [count]
#
# Arguments:
#   username_base: The prefix for generated usernames (e.g. 'bot').
#   password:      The password for all bots.
#   ride_code:     The 6-character ride code to join.
#   count:         (Optional) Number of bots to spawn. Default is 1.
#
# Helper Command (PowerShell):
#   python tests/debug_tools/ghost_rider.py swarm_user swarmpass [CODE] 5
# ------------------------------------------------------------------------------

BASE_URL = "http://127.0.0.1:8000"

async def get_token(session, username, password):
    async with session.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password}) as resp:
        if resp.status != 200:
            print(f"[{username}] Login failed: {await resp.text()}")
            return None
        data = await resp.json()
        return data["access_token"]

async def run_single_ghost(index, username, password, ride_code):
    """
    Runs a single ghost rider instance.
    """
    sio = socketio.AsyncClient()
    
    # Event Handlers for this specific client
    @sio.event
    async def connect():
        print(f"[{username}] Socket connected")

    @sio.event
    async def disconnect():
        print(f"[{username}] Socket disconnected")

    @sio.event
    async def location_update(data):
        # Optional: Print incoming updates (maybe too noisy for swarm)
        pass 

    print(f"[{username}] Starting...")

    async with aiohttp.ClientSession() as session:
        # 1. Login / Register
        token = await get_token(session, username, password)
        if not token:
            # Try registering
            print(f"[{username}] Attempting registration...")
            async with session.post(f"{BASE_URL}/users/", json={"username": username, "password": password}) as resp:
                if resp.status == 201:
                    token = await get_token(session, username, password)
                else:
                    print(f"[{username}] Registration failed: {await resp.text()}")
                    return

        if not token:
            print(f"[{username}] Could not authenticate.")
            return

        # 2. Get User ID
        user_id = None
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(f"{BASE_URL}/auth/me", headers=headers) as resp:
             if resp.status == 200:
                 me = await resp.json()
                 user_id = me["id"]
             else:
                 print(f"[{username}] Failed to get info.")
                 return

        # 3. Join Ride API
        async with session.post(f"{BASE_URL}/participations/", json={"ride_code": ride_code}, headers=headers) as resp:
            if resp.status in [201, 409]:
                print(f"[{username}] Joined ride {ride_code} (User ID: {user_id})")
            else:
                print(f"[{username}] Failed to join API: {resp.status}")
                return

        # 4. Connect Socket
        try:
            await sio.connect(BASE_URL, transports=['websocket', 'polling'])
            await sio.emit("join_ride", {"ride_code": ride_code})

            # Random Start Position (Munich Center + Offset)
            lat = 48.1351 + random.uniform(-0.005, 0.005)
            lon = 11.5820 + random.uniform(-0.005, 0.005)
            
            # Send INITIAL location (so they appear on map)
            payload = {
                "ride_code": ride_code,
                "user_id": user_id,
                "latitude": lat,
                "longitude": lon,
                "location_timestamp": None # Let server/client timestamp it
            }
            await sio.emit("update_location", payload) # Send once
            print(f"[{username}] Spawned at {lat:.4f}, {lon:.4f} (IDLE)")

            # IDLE LOOP: Just stay connected
            while True:
                await asyncio.sleep(10) # Just heartbeat/keepalive

        except asyncio.CancelledError:
            print(f"[{username}] Stopping...")
        except Exception as e:
            print(f"[{username}] Error: {e}")
        finally:
            if sio.connected:
                await sio.disconnect()


async def main():
    if len(sys.argv) < 3:
        print("Usage: python ghost_rider.py [user_base] [pass] [ride_code] [count=1]")
        return

    base_username = sys.argv[1]
    password = sys.argv[2]
    ride_code = sys.argv[3]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 1

    print(f"--- Spawning {count} Ghost Riders for ride {ride_code} ---")

    tasks = []
    for i in range(count):
        # If count > 1, append index to username to make unique
        uname = f"{base_username}_{i}" if count > 1 else base_username
        tasks.append(run_single_ghost(i, uname, password, ride_code))

    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Main Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Graceful exit for windows loop issues
        pass
