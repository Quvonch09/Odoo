from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        await session.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"))
        yield session


async def get_rw_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        await session.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE"))
        yield session


async def ping_database() -> bool:
    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))
    return True


async def close_db() -> None:
    await engine.dispose()
