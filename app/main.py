from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import socketio

import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

from app import routers
from app.models import DbModel

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    print("Startup: Initializing database engine")
    database_url = os.getenv("DATABASE_URL", "sqlite:///ride.db")

    if database_url.startswith("postgresql"):
        app.state.database_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            )
        print(f"(SUCCESS) Connected to PostgreSQL")
    else:
        app.state.database_engine = create_engine(database_url)
        print(f"(SUCCESS) Connected to SQLite")
        
    DbModel.metadata.create_all(bind=app.state.database_engine)
    yield

    print("Shutdown: Disposing database engine")
    if app.state.database_engine:
        app.state.database_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ride App API",
        version="0.1.3",
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
    # This wraps the FastAPI app with the Socket.IO ASGI app handler
    # socket_app works as the main entry point
    socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
    
    return socket_app


app = create_app()