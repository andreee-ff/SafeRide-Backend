import asyncio
import socketio
import aiohttp
import sys
import json
import random

# Ghost Rider: Simulates a moving user on a ride
# Usage: python tests/debug_tools/ghost_rider.py [username] [password] [ride_code]

BASE_URL = "http://localhost:8000"
sio = socketio.AsyncClient()

async def get_token(session, username, password):
    async with session.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password}) as resp:
        if resp.status != 200:
            print(f"Login failed: {await resp.text()}")
            return None
        data = await resp.json()
        return data["access_token"]

@sio.event
async def connect():
    print("Socket.IO connected")

@sio.event
async def location_update(data):
    print(f"Received location update: {data}")

@sio.event
async def disconnect():
    print("Socket.IO disconnected")

async def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "ghost_rider"
    password = sys.argv[2] if len(sys.argv) > 2 else "ghostpass"
    ride_code = sys.argv[3] if len(sys.argv) > 3 else "ABC123"

    print(f"Starting Ghost Rider as {username} for ride {ride_code}...")

    async with aiohttp.ClientSession() as session:
        # 1. Login
        token = await get_token(session, username, password)
        if not token:
            # Try registering if login fails
            print("Login failed, attempting registration...")
            async with session.post(f"{BASE_URL}/users/", json={"username": username, "password": password}) as resp:
                if resp.status == 201:
                    print("Registered successfully.")
                    token = await get_token(session, username, password)
                else:
                    print(f"Registration failed: {await resp.text()}")
                    return

        if not token:
            print("Could not authenticate.")
            return

        print(f"Authenticated. Token: {token[:10]}...")

        # 2. Connect to Socket.IO
        try:
            # Sending token in headers or auth payload depending on server config
            # Here assuming server checks headers or auth packet.
            # Using 'auth' for best python-socketio compatibility
            await sio.connect(BASE_URL, auth={"token": token})
            
            # 3. Join Ride Room
            print(f"Joining ride {ride_code}...")
            await sio.emit("join_ride", {"ride_code": ride_code})

            # 4. Loop location updates
            # Start at some coordinates (e.g. Munich)
            lat = 48.1351
            lon = 11.5820
            
            print("Starting movement simulation (Ctrl+C to stop)...")
            while True:
                # Simulate movement
                lat += random.uniform(-0.001, 0.001)
                lon += random.uniform(-0.001, 0.001)
                
                payload = {
                    "ride_code": ride_code,
                    "latitude": lat,
                    "longitude": lon
                }
                
                await sio.emit("update_location", payload)
                print(f"Sent update: {lat:.4f}, {lon:.4f}")
                
                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print("\nStopping...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if sio.connected:
                await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
