import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import DbModel

load_dotenv()

database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///ride.db")

if database_url.startswith("sqlite")  and "aiosqlite" not in database_url:
    database_url = database_url.replace("sqlite", "sqlite+aiosqlite")
elif database_url.startswith("postgresql") and "asyncpg" not in database_url:
    database_url = database_url.replace("postgresql", "postgresql+asyncpg")

engine = create_async_engine(
    database_url,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(DbModel.metadata.create_all)