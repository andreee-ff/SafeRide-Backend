from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models import RouteModel
from app.utils.geo import calculate_gpx_distance

class RouteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_routes(self) -> Sequence[RouteModel]:
        statement = select(RouteModel)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_id(self, *, route_id: int) -> RouteModel | None:
        statement = select(RouteModel).where(RouteModel.id == route_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_owned_routes(self, user_id: int) -> Sequence[RouteModel]:
        statement = (
            select(RouteModel)
            .where(RouteModel.created_by_user_id == user_id)
            .order_by(RouteModel.created_at.desc())
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

# ------------- CREATE ------------- #

    async def create_route(
        self, 
        *,
        title: str, 
        description: str | None,
        gpx_data: str, 
        created_by_user_id: int,
        distance_meters: float = 0.0
    ) -> RouteModel:
        if distance_meters == 0.0:
            distance_meters = calculate_gpx_distance(gpx_data)

        route = RouteModel(
            title=title,
            description=description,
            gpx_data=gpx_data,
            created_by_user_id=created_by_user_id,
            distance_meters=distance_meters
        )
        self.session.add(route)
        await self.session.flush()
        await self.session.refresh(route)
        return route

# ------------- UPDATE ------------- #

    async def update_route(
        self,
        route: RouteModel,
        *, 
        title: str | None = None,
        description: str | None = None,
        gpx_data: str | None = None,
        distance_meters: float | None = None
    ) -> RouteModel | None:
        route_to_update ={
            "title": title,
            "description": description,
            "gpx_data": gpx_data,
            "distance_meters": distance_meters
        }

        for key, value in route_to_update.items():
            if value is not None:
                setattr(route, key, value)

        self.session.add(route)
        await self.session.flush()
        await self.session.refresh(route)
        return route

# ------------- DELETE ------------- #

    async def delete_route(self, *,route: RouteModel) -> None:
        await self.session.delete(route)
        await self.session.flush()
