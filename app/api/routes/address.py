from fastapi import APIRouter
from app.schemas.address import (
    NavigationRequest,
    NavigationResponse,
)

from app.services.navigation_resolver import (
    NavigationResolver,
)
from app.nlp.normalizer import normalize_arabic_address
from app.nlp.parser import parse_descriptive_address

from app.schemas.address import (
    AddressParseRequest,
    AddressParseResponse,
    AddressResolveResponse,
)

from app.services.delivery_route_service import (
    build_delivery_routes,
)


router = APIRouter()


@router.post(
    "/parse",
    response_model=AddressParseResponse,
)
def parse_address(
    payload: AddressParseRequest,
) -> AddressParseResponse:

    normalized = normalize_arabic_address(
        payload.address
    )

    parsed = parse_descriptive_address(
        payload.address
    )

    return AddressParseResponse(
        raw_address=payload.address,
        normalized_address=normalized,
        parser_version="rule-parser-v0.2",
        administrative_areas=parsed[
            "administrative_areas"
        ],
        street=parsed["street"],
        landmarks=parsed["landmarks"],
        directions=parsed["directions"],
        building=parsed["building"],
        unresolved_terms=parsed[
            "unresolved_terms"
        ],
        overall_confidence=parsed[
            "overall_confidence"
        ],
    )


@router.post(
    "/resolve",
    response_model=AddressResolveResponse,
)
def resolve_address(
    payload: AddressParseRequest,
) -> AddressResolveResponse:

    normalized = normalize_arabic_address(
        payload.address
    )

    parsed = parse_descriptive_address(
        payload.address
    )

    routing = build_delivery_routes(
        parsed
    )

    destination = routing["destination"]
    recommended_route = routing["recommended_route"]

    summary = {
        "destination": (
            f'{destination["name"]} - {destination["area"]}'
            if destination
            else None
        ),
        "latitude": (
            destination["latitude"]
            if destination
            else None
        ),
        "longitude": (
            destination["longitude"]
            if destination
            else None
        ),
        "best_route": (
            recommended_route["route_name"]
            if recommended_route
            else None
        ),
        "estimated_time_minutes": (
            recommended_route["duration_minutes"]
            if recommended_route
            else None
        ),
        "checkpoint": (
            recommended_route["checkpoints"][0]["checkpoint"]
            if recommended_route
            and recommended_route.get("checkpoints")
            else None
        ),
        "checkpoint_status": (
            recommended_route["checkpoints"][0]["status"]
            if recommended_route
            and recommended_route.get("checkpoints")
            else None
        ),
        "decision": (
            recommended_route["recommendation"]
            if recommended_route
            else "لم يتم العثور على مسار مناسب"
        ),
    }

    return AddressResolveResponse(
        raw_address=payload.address,
        normalized_address=normalized,
        parser_version="rule-parser-v0.2",
        administrative_areas=parsed[
            "administrative_areas"
        ],
        destination=routing[
            "destination"
        ],
        routing_mode=routing[
            "routing_mode"
        ],
        checkpoint_source=routing[
            "checkpoint_source"
        ],
        simulation=routing[
            "simulation"
        ],
        summary=summary,
        recommended_route=routing[
            "recommended_route"
        ],
        routes=routing[
            "routes"
        ],
    )
@router.post(
    "/navigate",
    response_model=NavigationResponse,
)
def navigate_address(
    payload: NavigationRequest,
) -> NavigationResponse:

    resolver = NavigationResolver(
        radius_meters=1500,
    )

    result = resolver.resolve(
        payload.address
    )

    return NavigationResponse(
        status=result.get(
            "status",
            "unknown",
        ),

        raw_address=result.get(
            "raw_address",
            payload.address,
        ),

        administrative_area=result.get(
            "administrative_area"
        ),

        anchor=result.get(
            "anchor"
        ),

        instructions=result.get(
            "instructions",
            [],
        ),

        validation_landmarks=result.get(
            "validation_landmarks",
            [],
        ),

        final_destination=result.get(
            "final_destination"
        ),

        final_confidence=result.get(
            "final_confidence"
        ),

        ambiguous=result.get(
            "ambiguous",
            False,
        ),

        best_candidate=result.get(
            "best_candidate"
        ),
    )
