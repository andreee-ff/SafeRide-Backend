import socketio
from datetime import datetime

from app.services import LocationService

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def join_ride(sid, data):
    """
    Client joins a ride "room" to receive updates.
    data: {'ride_code': 'ABC123'}
    """
    ride_code = data.get('ride_code')
    if not ride_code:
        return

    # Validate ride
    exist = await LocationService.validate_ride(ride_code=ride_code)
    if not exist:
        await sio.emit('error', {'msg': f'Ride {ride_code} not found'}, room=sid)
        return  
    
    # Join ride room
    await sio.enter_room(sid, ride_code)
    await sio.emit('message', {'msg': f'Joined ride {ride_code}'}, room=sid)

@sio.event
async def update_location(sid, data):
    """
    1. Validate input
    2. Broadcast to room (FAST!)
    3. Save to DB (ASYNC BACKGROUND)
    
    Client sends new GPS coordinates.
    data: {
        'ride_code': 'ABC123',
        'user_id': 1,
        'latitude': 55.755, 
        'longitude': 37.625
    }
    """
    ride_code = data.get('ride_code')
    user_id = data.get('user_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    location_timestamp = data.get('location_timestamp')
    
    if not (ride_code and user_id and latitude and longitude):
        return

    if not location_timestamp:
        location_timestamp = datetime.utcnow().isoformat()

    # 1. BROADCAST 
    await sio.emit('location_update', {
        'user_id': user_id,
        'latitude': latitude,
        'longitude': longitude,
        'location_timestamp': location_timestamp
    }, room=ride_code)

    # 2. Save to DB (async background)
    try:
        await LocationService.process_location_update(
            user_id=user_id,
            ride_code=ride_code,
            latitude=latitude,
            longitude=longitude,
            location_timestamp=location_timestamp
        )
    except ValueError as e:
        print(f"Error processing location update: {e}")
        await sio.emit('error', {'msg': str(e)}, room=sid)
    
    except Exception as e:
        print(f"Unexpected error: {e}")
