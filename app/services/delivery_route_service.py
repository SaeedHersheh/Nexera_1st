from app.integrations.aween_rayeh import AweenRayehClient
from app.services.checkpoint_analyzer import analyze_checkpoint
from app.services.route_scorer import rank_routes


CITY_SLUGS = {
    "جنين": "jenin",
    "رام الله": "ramallah",
    "نابلس": "nablus",
    "الخليل": "hebron",
    "بيت لحم": "bethlehem",
    "طولكرم": "tulkarm",
    "القدس": "jerusalem",
    "قلقيلية": "qalqilya",
    "اريحا": "jericho",
    "أريحا": "jericho",
    "سلفيت": "salfit",
    "طوباس": "tubas",
}


# مؤقت فقط للـSimulation.
# لاحقًا Google Maps / routing engine سيعطينا الوقت الحقيقي.
SIMULATED_ROUTE_DURATIONS = {
    "حاجز الجلمة": 28,
    "حاجز دوتان": 22,
    "حاجز برطعة": 18,
}


def _find_city_slug(administrative_areas: dict) -> str:
    """
    Convert detected Arabic administrative area
    to the city slug expected by Aween Rayeh.
    """

    for key in (
        "city",
        "governorate",
        "locality",
        "neighborhood",
    ):
        value = administrative_areas.get(key)

        if value in CITY_SLUGS:
            return CITY_SLUGS[value]

    # Current proof of concept focuses on Jenin.
    return "jenin"


def _find_best_destination(parsed_address: dict) -> dict | None:
    landmarks = parsed_address.get("landmarks", [])

    matched_landmarks = [
        landmark
        for landmark in landmarks
        if landmark.get("place_id") is not None
    ]

    if not matched_landmarks:
        return None

    best = max(
        matched_landmarks,
        key=lambda landmark: landmark.get(
            "match_score",
            0.0,
        ),
    )

    return {
        "place_id": best.get("place_id"),
        "name": best.get("matched_name"),
        "original_landmark": best.get("text"),
        "area": best.get("matched_area"),
        "latitude": best.get("latitude"),
        "longitude": best.get("longitude"),
        "match_score": best.get("match_score"),
        "matched_by": best.get("matched_by"),
    }


def build_delivery_routes(parsed_address: dict) -> dict:
    city_slug = _find_city_slug(
        parsed_address["administrative_areas"]
    )

    destination = _find_best_destination(
        parsed_address
    )

    client = AweenRayehClient()

    checkpoint_response = client.get_city_checkpoints(
        city_slug
    )

    checkpoints = checkpoint_response.get(
        "data",
        [],
    )

    routes = []

    for index, checkpoint in enumerate(checkpoints):
        analyzed_checkpoint = analyze_checkpoint(
            checkpoint,
            direction="entering",
        )

        checkpoint_name = checkpoint.get(
            "checkpoint",
            f"checkpoint_{index + 1}",
        )

        duration = SIMULATED_ROUTE_DURATIONS.get(
            checkpoint_name,
            25 + (index * 5),
        )

        routes.append(
            {
                "route_id": f"route_{index + 1}",
                "route_name": f"المسار عبر {checkpoint_name}",
                "duration_minutes": duration,
                "checkpoints": [
                    analyzed_checkpoint,
                ],
            }
        )

    ranked_routes = rank_routes(routes)

    recommended_route = (
        ranked_routes[0]
        if ranked_routes
        else None
    )

    simulation = checkpoint_response.get(
        "meta",
        {},
    ).get(
        "simulation",
        False,
    )

    return {
        "destination": destination,
        "city": city_slug,
        "routing_mode": "simulation",
        "checkpoint_source": (
            "aween_rayeh_simulation"
            if simulation
            else "aween_rayeh_live"
        ),
        "simulation": simulation,
        "recommended_route": recommended_route,
        "routes": ranked_routes,
    }
