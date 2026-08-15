from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.address import router as address_router
from app.api.routes.intelligence import router as intelligence_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "Palestinian descriptive-address "
        "and navigation intelligence engine"
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    address_router,
    prefix="/api/v1/address",
    tags=["address"],
)


app.include_router(
    intelligence_router,
    prefix="/api/v1/intelligence",
    tags=["intelligence"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.2.0",
    }
