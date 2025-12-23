from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import socketio

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import routers
from app.database import engine, init_db

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    print("Startup: Initializing database...")

    await init_db()
    print("Startup: (SUCCESS) Database initialized")
    yield

    print("Shutdown: Disposing database engine...")
    await engine.dispose()
    
    print("Shutdown: (SUCCESS) Database disposed")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Ride App API (Async)",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        routers.user_router,
        prefix="/users",
        tags=["Users, Registration"],
    )

    app.include_router(
        routers.auth_router,
        prefix="/auth",
        tags=["Authentication"],
    )

    app.include_router(
        routers.ride_router,
        prefix="/rides",
        tags=["Rides"],
    )

    app.include_router(
        routers.route_router,
        prefix="/routes",
        tags=["Routes"],
    )

    app.include_router(
        routers.participation_router,
        prefix="/participations",
        tags=["Participation"],
    )

    app.include_router(
        routers.simulation_router,
        prefix="/simulation",
        tags=["Debug & Tools"],
    )

    # Mount Socket.IO
    from app.sockets import sio
    socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
    
    return socket_app


app = create_app()