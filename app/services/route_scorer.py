def calculate_route_score(
    duration_minutes: float,
    checkpoint_analyses: list[dict],
):
    """
    Lower score = better route.
    """

    checkpoint_score = sum(
        checkpoint.get("score", 0)
        for checkpoint in checkpoint_analyses
    )

    has_closed_checkpoint = any(
        checkpoint.get("status") == "مغلق"
        for checkpoint in checkpoint_analyses
    )

    if has_closed_checkpoint:
        return {
            "score": 9999,
            "duration_minutes": duration_minutes,
            "checkpoint_score": checkpoint_score,
            "blocked": True,
            "recommendation": "المسار غير مناسب بسبب وجود حاجز مغلق",
        }

    total_score = duration_minutes + (checkpoint_score * 5)

    if checkpoint_score == 0:
        recommendation = "المسار مناسب"

    elif checkpoint_score <= 2:
        recommendation = "المسار جيد مع تأخير بسيط محتمل"

    elif checkpoint_score <= 5:
        recommendation = "يوجد ازدحام، افحص البدائل"

    else:
        recommendation = "يفضل اختيار مسار بديل"

    return {
        "score": round(total_score, 2),
        "duration_minutes": duration_minutes,
        "checkpoint_score": checkpoint_score,
        "blocked": False,
        "recommendation": recommendation,
    }


def rank_routes(routes: list[dict]):
    analyzed_routes = []

    for route in routes:
        result = calculate_route_score(
            duration_minutes=route["duration_minutes"],
            checkpoint_analyses=route.get("checkpoints", []),
        )

        analyzed_routes.append(
            {
                "route_id": route["route_id"],
                "route_name": route.get(
                    "route_name",
                    route["route_id"],
                ),
                "checkpoints": route.get("checkpoints", []),
                **result,
            }
        )

    analyzed_routes.sort(
        key=lambda route: route["score"]
    )

    for index, route in enumerate(
        analyzed_routes,
        start=1,
    ):
        route["rank"] = index
        route["recommended"] = index == 1

    return analyzed_routes
