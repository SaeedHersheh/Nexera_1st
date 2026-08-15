def resolve_anchor(parsed_address: dict) -> dict | None:
    landmarks = parsed_address.get("landmarks", [])

    candidates = [
        landmark
        for landmark in landmarks
        if landmark.get("place_id") is not None
    ]

    if not candidates:
        return None

    best = max(
        candidates,
        key=lambda item: (
            item.get("match_score", 0.0),
            item.get("database_confidence", 0.0) or 0.0,
        ),
    )

    return {
        "place_id": best.get("place_id"),
        "name": best.get("matched_name"),
        "original_text": best.get("text"),
        "type": best.get("type"),
        "relation": best.get("relation"),
        "area": best.get("matched_area"),
        "latitude": best.get("latitude"),
        "longitude": best.get("longitude"),
        "match_score": best.get("match_score"),
        "position": best.get("position"),
    }
