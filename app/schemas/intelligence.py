from typing import Any

from pydantic import BaseModel, Field


class FullIntelligenceRequest(BaseModel):
    address: str = Field(
        min_length=2,
        max_length=2000,
    )


class FullIntelligenceResponse(BaseModel):
    status: str

    raw_address: str

    summary: dict[
        str,
        Any,
    ] | None = None

    navigation: dict[
        str,
        Any,
    ] | None = None

    pathfinding: dict[
        str,
        Any,
    ] | None = None

    delivery_routing: dict[
        str,
        Any,
    ] | None = None

    stage_failed: str | None = None
