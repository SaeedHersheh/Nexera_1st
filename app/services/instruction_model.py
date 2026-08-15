from app.services.anchor_resolver import resolve_anchor


def build_instruction_model(parsed_address: dict) -> dict:
    anchor = resolve_anchor(parsed_address)

    instructions = []

    for direction in parsed_address.get("directions", []):
        if direction.get("instruction") == "turn":
            instructions.append(
                {
                    "type": "turn",
                    "order": direction.get("order"),
                    "direction": direction.get("direction"),
                    "raw_text": direction.get("raw_text"),
                    "position": direction.get("position", 999999),
                    "confidence": direction.get("confidence"),
                }
            )

        elif direction.get("instruction") == "direction":
            instructions.append(
                {
                    "type": "direction",
                    "direction": direction.get("direction"),
                    "raw_text": direction.get("raw_text"),
                    "position": direction.get("position", 999999),
                    "confidence": direction.get("confidence"),
                }
            )

    for distance in parsed_address.get("distances", []):
        instructions.append(
            {
                "type": "distance",
                "meters": distance.get("meters"),
                "raw_text": distance.get("raw_text"),
                "position": distance.get("position", 999999),
                "confidence": distance.get("confidence"),
            }
        )

    instructions.sort(
        key=lambda item: item.get("position", 999999)
    )

    return {
        "anchor": anchor,
        "anchor_relation": (
            anchor.get("relation")
            if anchor
            else None
        ),
        "instructions": instructions,
        "instruction_count": len(instructions),
    }
