from app.routers.auth import router as auth_router
from app.routers.users import router as user_router
from app.routers.rides import router as ride_router
from app.routers.routes import router as route_router
from app.routers.participations import router as participation_router
from app.routers.simulation import router as simulation_router

__all__ = [
    "auth_router",
    "user_router", 
    "ride_router",
    "route_router",
    "participation_router",
    "simulation_router",
]