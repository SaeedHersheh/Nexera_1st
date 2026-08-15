STATUS_SCORES = {
    "سالك": 0,
    "خفيف": 1,
    "أزمة": 5,
    "مغلق": 10,
}


def analyze_checkpoint(checkpoint: dict, direction: str = "entering"):
    if direction == "leaving":
        status = checkpoint.get("leaving_status")
    else:
        status = checkpoint.get("entering_status")

    score = STATUS_SCORES.get(status, 3)

    if status == "سالك":
        recommendation = "الطريق مناسب"
        severity = "low"

    elif status == "خفيف":
        recommendation = "يمكن المرور مع تأخير بسيط"
        severity = "low"

    elif status == "أزمة":
        recommendation = "يفضل البحث عن مسار بديل"
        severity = "medium"

    elif status == "مغلق":
        recommendation = "تجنب هذا الحاجز واستخدم مسار بديل"
        severity = "high"

    else:
        recommendation = "حالة الحاجز غير واضحة"
        severity = "unknown"

    return {
        "checkpoint_id": checkpoint.get("id"),
        "checkpoint": checkpoint.get("checkpoint"),
        "city": checkpoint.get("city"),
        "direction": direction,
        "status": status,
        "score": score,
        "severity": severity,
        "recommendation": recommendation,
        "last_updated": checkpoint.get("last_updated"),
    }


def analyze_city_checkpoints(api_response: dict, direction: str = "entering"):
    results = []

    for checkpoint in api_response.get("data", []):
        analyzed = analyze_checkpoint(
            checkpoint,
            direction=direction,
        )

        results.append(analyzed)

    return results
