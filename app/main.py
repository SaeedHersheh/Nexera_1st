from fastapi import FastAPI

from app.api.routes.address import router as address_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Palestinian descriptive-address understanding service",
)

app.include_router(address_router, prefix="/api/v1/address", tags=["address"])


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.1.0",
    }
