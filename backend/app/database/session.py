from collections.abc import AsyncIterator

from sqlalchemy import URL, make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def build_database_url(settings: Settings) -> URL:
    if settings.database_url is not None:
        database_url = make_url(settings.database_url.get_secret_value())
        supported_drivers = {
            "postgres",
            "postgresql",
            "postgresql+psycopg",
            "postgresql+psycopg_async",
        }

        if database_url.drivername not in supported_drivers:
            raise ValueError("DATABASE_URL must use PostgreSQL")

        return database_url.set(drivername="postgresql+psycopg_async")

    if settings.database_password is None:
        raise ValueError("DATABASE_PASSWORD is required when DATABASE_URL is not set")

    return URL.create(
        drivername="postgresql+psycopg_async",
        username=settings.database_user,
        password=settings.database_password.get_secret_value(),
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
    )


def create_database_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        build_database_url(settings),
        pool_pre_ping=True,
    )


database_engine = create_database_engine(get_settings())

async_session_factory = async_sessionmaker(
    bind=database_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_database_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def check_database_connection() -> bool:
    async with database_engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    return result.scalar_one() == 1
