from typing import Any

from pydantic import BaseModel, Field


class AddressParseRequest(BaseModel):
    address: str = Field(min_length=2, max_length=2000)


class AddressParseResponse(BaseModel):
    raw_address: str
    normalized_address: str
    parser_version: str

    administrative_areas: dict[str, str | None]
    street: str | None

    landmarks: list[dict[str, Any]]
    directions: list[dict[str, Any]]
    building: dict[str, Any]

    unresolved_terms: list[str]

    overall_confidence: float = Field(ge=0.0, le=1.0)
class AddressResolveResponse(BaseModel):
    raw_address: str
    normalized_address: str
    parser_version: str

    administrative_areas: dict[str, str | None]

    destination: dict[str, Any] | None

    routing_mode: str
    checkpoint_source: str
    simulation: bool
    summary: dict[str, Any]
    recommended_route: dict[str, Any] | None
    routes: list[dict[str, Any]]
