from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/meta", tags=["meta"])

@router.get("")
async def metadata() -> dict[str, str]:
    return {"name": settings.app_name, "environment": settings.app_env, "api_version": "v1"}
