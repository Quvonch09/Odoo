from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security import AnalyticsAPIKey, AnalyticsUser


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> AnalyticsUser | None:
        return await self.session.scalar(select(AnalyticsUser).where(AnalyticsUser.email == email))

    async def create_user(self, user: AnalyticsUser) -> AnalyticsUser:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_api_key(self, api_key: AnalyticsAPIKey) -> AnalyticsAPIKey:
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key

    async def get_api_key(self, key_hash: str) -> AnalyticsAPIKey | None:
        return await self.session.scalar(select(AnalyticsAPIKey).where(AnalyticsAPIKey.key_hash == key_hash))

    async def get_user_by_id(self, user_id: int) -> AnalyticsUser | None:
        return await self.session.get(AnalyticsUser, user_id)

    async def touch_api_key(self, api_key: AnalyticsAPIKey) -> None:
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.session.commit()
