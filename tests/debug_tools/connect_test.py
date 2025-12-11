import asyncio
import socketio

# Simple connection test script
# Usage: python tests/debug_tools/connect_test.py

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("connection established")

@sio.event
async def message(data):
    print('message received with ', data)

@sio.event
async def disconnect():
    print('disconnected from server')

async def main():
    try:
        print("Attempting to connect to http://localhost:8000...")
        await sio.connect('http://localhost:8000')
        print("Connected! Sending join_ride event...")
        await sio.emit('join_ride', {'ride_code': 'ABC123'})
        await sio.sleep(1)
        await sio.disconnect()
        print("Disconnected.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
