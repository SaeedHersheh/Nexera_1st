from fastapi import APIRouter

from app.schemas.intelligence import (
    FullIntelligenceRequest,
    FullIntelligenceResponse,
)

from app.services.full_intelligence_service import (
    FullIntelligenceService,
)


router = APIRouter()


@router.post(
    "/resolve",
    response_model=FullIntelligenceResponse,
)
def full_resolve(
    payload: FullIntelligenceRequest,
) -> FullIntelligenceResponse:

    service = FullIntelligenceService(
        radius_meters=1500,
    )

    result = service.resolve(
        payload.address
    )

    return FullIntelligenceResponse(
        **result
    )
