
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.employees import router as employees_router
from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.api.routes.meta import router as meta_router
from app.api.routes.auth import router as auth_router
from app.api.routes.risk_scores import router as risk_scores_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.investigations import router as investigations_router

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="AI-assisted insider-threat detection and investigation platform.",
)

# Allow the local React frontend to communicate with the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(meta_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(employees_router, prefix=settings.api_v1_prefix)
app.include_router(events_router, prefix=settings.api_v1_prefix)
app.include_router(risk_scores_router, prefix=settings.api_v1_prefix)
app.include_router(alerts_router, prefix=settings.api_v1_prefix)
app.include_router(investigations_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}
