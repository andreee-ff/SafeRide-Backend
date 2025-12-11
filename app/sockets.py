import socketio
from datetime import datetime
# Circular imports removed for MVP
# from app.injections import get_participation_repository, get_ride_repository
# from app.repositories import ParticipationRepository, RideRepository
# from app.database import SessionLocal

# Create a Socket.IO server
# async_mode='asgi' is crucial for integration with FastAPI
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
    
    # In a real app, we might validate the code exists here, 
    # but for speed, we just join the room named by the code.
    sio.enter_room(sid, ride_code)
    print(f"Client {sid} joined room {ride_code}")
    print(f"DEBUG: Rooms for {sid}: {sio.rooms(sid)}")
    await sio.emit('message', {'msg': f'Joined ride {ride_code}'}, room=sid)

@sio.event
async def update_location(sid, data):
    print(f"DEBUG: update_location handler called with {data}")
    """
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
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    if not (ride_code and user_id and lat and lng):
        return

    # Broadcast to everyone in the room EXCEPT sender
    # We send the full participant-like object so frontend updates map effortlessly
    
    # NOTE: In a perfect world, we'd save to DB here asynchronously.
    # For now, we trust the frontend also calls the API or we do it here.
    # To keeps things fast and simple as requested "like the Flask example":
    # 1. Save to DB (optional optimization: fire and forget)
    # 2. Broadcast
    
    # Let's do a quick mock save
    try:
        # db = SessionLocal()
        # repo = ParticipationRepository(db)
        
        # DEBUG: Check participants
        # Note: get_participants might be async or sync depending on manager, usually sync for InMemory
        # For AsyncServer, usually we can just inspect if using InMemoryManager
        # But there isn't a direct public API for participants in async server always simple.
        # Let's try global emit instead to prove broadcasting works.
        
        print(f"DEBUG: Broadcasting to ROOM {ride_code}")
        await sio.emit('message', {'msg': f'DEBUG: Broadcast to room {ride_code}'}, room=ride_code)
        
        print(f"DEBUG: Broadcasting GLOBALLY")
        await sio.emit('message', {'msg': f'DEBUG: GLOBAL BROADCAST'})
        
        await sio.emit('location_update', {
            'user_id': user_id,
            'latitude': lat,
            'longitude': lng,
            'location_timestamp': datetime.utcnow().isoformat()
        }, room=ride_code)
        
        print(f"Location update for user {user_id} in ride {ride_code}: {lat}, {lng}")
        
    except Exception as e:
        print(f"Error in socket update: {e}")
    # finally:
    #    db.close()
