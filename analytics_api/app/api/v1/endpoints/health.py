from fastapi import APIRouter

from app.core.responses import success_response
from app.db.session import ping_database
from app.services.cache_service import ping_redis

router = APIRouter()


@router.get("/health/live")
async def live():
    return success_response(message="Service is alive", data={"status": "alive"})


@router.get("/health/ready")
async def ready():
    db_ok = await ping_database()
    redis_ok = await ping_redis()
    return success_response(
        message="Readiness checked",
        data={"database": db_ok, "redis": redis_ok, "ready": db_ok and redis_ok},
    )
