from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from redis.asyncio import Redis
from app.core.config import settings
from app.db.session import engine

router = APIRouter(tags=["health"])

@router.get("/health/live", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}

@router.get("/health/ready", summary="Readiness probe")
async def readiness() -> dict[str, str]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        redis = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        try:
            await redis.ping()
        finally:
            await redis.aclose()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="A required dependency is unavailable") from exc
    return {"status": "ready", "database": "ok", "redis": "ok"}
