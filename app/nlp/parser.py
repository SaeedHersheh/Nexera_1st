import re

from app.nlp.normalizer import normalize_arabic_address
from app.db.admin_area_repository import detect_administrative_areas
from app.db.place_repository import match_place


# المرحلة الأولى:
# قاموس صغير فقط لإثبات الفكرة.
# لاحقًا سنستبدله بقاعدة البيانات PostgreSQL/PostGIS.

LANDMARK_TYPES = {
    "مسجد": "mosque",
    "جامع": "mosque",
    "مدرسة": "school",
    "جامعة": "university",
    "مستشفى": "hospital",
    "صيدلية": "pharmacy",
    "بنك": "bank",
    "دوار": "roundabout",
    "مخبز": "bakery",
    "سوبرماركت": "shop",
    "بقالة": "shop",
    "دكان": "shop",
    "مطعم": "restaurant",
}


RELATIONS = {
    "بعد": "after",
    "قبل": "before",
    "جنب": "next_to",
    "بجانب": "next_to",
    "مقابل": "opposite",
    "عند": "at",
    "قرب": "near",
    "قريب من": "near",
    "ورا": "behind",
    "وراء": "behind",
    "قدام": "in_front_of",
    "أمام": "in_front_of",
}


DIRECTION_MAP = {
    "يمين": "right",
    "عاليمين": "right",
    "ع اليمين": "right",
    "يسار": "left",
    "الشمال": "north",
    "شمال": "north",
    "الجنوب": "south",
    "جنوب": "south",
    "الشرق": "east",
    "شرق": "east",
    "الغرب": "west",
    "غرب": "west",
}


ORDINAL_MAP = {
    "أول": 1,
    "اول": 1,
    "ثاني": 2,
    "ثالث": 3,
    "رابع": 4,
}


BUILDING_COLORS = {
    "الأبيض": "أبيض",
    "الابيض": "أبيض",
    "أبيض": "أبيض",
    "ابيض": "أبيض",
    "الأسود": "أسود",
    "الاسود": "أسود",
    "أسود": "أسود",
    "احمر": "أحمر",
    "أحمر": "أحمر",
    "الأحمر": "أحمر",
    "الاخضر": "أخضر",
    "الأخضر": "أخضر",
    "اخضر": "أخضر",
    "أخضر": "أخضر",
    "الأزرق": "أزرق",
    "الازرق": "أزرق",
    "أزرق": "أزرق",
    "ازرق": "أزرق",
}


STOP_WORDS = {
    "بعد",
    "قبل",
    "جنب",
    "بجانب",
    "مقابل",
    "عند",
    "قرب",
    "ورا",
    "وراء",
    "قدام",
    "أمام",
    "اول",
    "أول",
    "ثاني",
    "ثالث",
    "رابع",
    "يمين",
    "يسار",
    "عاليمين",
    "الشمال",
    "الجنوب",
    "الشرق",
    "الغرب",
    "البيت",
    "المنزل",
}


def _clean_token(token: str) -> str:
    return token.strip("،,.؛;:()[]{}")


def _landmark_type_for_token(token: str) -> str | None:
    """
    Match landmark words with or without Arabic definite article (ال).
    Examples:
    مسجد / المسجد
    صيدلية / الصيدلية
    سوبرماركت / السوبرماركت
    """
    token = _clean_token(token)

    if token in LANDMARK_TYPES:
        return LANDMARK_TYPES[token]

    if token.startswith("ال") and len(token) > 2:
        without_article = token[2:]

        if without_article in LANDMARK_TYPES:
            return LANDMARK_TYPES[without_article]

    return None



def _relation_before(text: str, landmark: str) -> str | None:
    position = text.find(landmark)

    if position == -1:
        return None

    before = text[max(0, position - 25):position]

    for arabic, normalized in sorted(
        RELATIONS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if arabic in before:
            return normalized

    return None


def _extract_landmarks(text: str) -> list[dict]:
    tokens = [_clean_token(token) for token in text.split()]
    landmarks = []

    i = 0

    while i < len(tokens):
        token = tokens[i]

        landmark_type = _landmark_type_for_token(token)

        if landmark_type is None:
            i += 1
            continue

        collected = [token]

        j = i + 1

        while j < len(tokens) and len(collected) < 4:
            current = _clean_token(tokens[j])

            if not current:
                break

            if current in STOP_WORDS:
                break

            if _landmark_type_for_token(current) is not None:
                break

            collected.append(current)
            j += 1

        landmark_text = " ".join(collected).strip()

        landmarks.append(
            {
                 "text": landmark_text,
        "type": landmark_type,
        "relation": _relation_before(text, landmark_text),
        "position": text.find(landmark_text),
        "confidence": 0.85,
            }
        )

        i = max(i + 1, j)

    return landmarks


def _extract_directions(text: str) -> list[dict]:
    directions = []

    turn_pattern = re.compile(
        r"(أول|اول|ثاني|ثالث|رابع)\s+"
        r"(?:دخلة|مدخل|شارع|لفة|لفه|طريق)"
        r"(?:\s+(?:ع|على))?\s*"
        r"(اليمين|يمين|اليسار|يسار|عاليمين)?"
    )

    for match in turn_pattern.finditer(text):
        ordinal_text = match.group(1)
        direction_text = match.group(2)

        normalized_direction = None

        if direction_text:
            direction_text = direction_text.replace("اليمين", "يمين")
            direction_text = direction_text.replace("اليسار", "يسار")
            normalized_direction = DIRECTION_MAP.get(direction_text)

        directions.append(
            {
                "instruction": "turn",
                "order": ORDINAL_MAP.get(ordinal_text),
                "direction": normalized_direction,
                "position": match.start(),
                "raw_text": match.group(0),
                "confidence": 0.90,
            }
        )

    if not directions:
        for arabic, normalized in DIRECTION_MAP.items():
            if arabic in text:
                directions.append(
                    {
                        "instruction": "direction",
                        "order": None,
                        "direction": normalized,
                        "raw_text": arabic,
                        "confidence": 0.75,
                    }
                )
                break

    return directions


def _extract_building(text: str) -> dict:
    building = {
        "type": None,
        "color": None,
        "number": None,
        "floor": None,
    }

    if "البيت" in text or "بيت " in text:
        building["type"] = "house"
    elif "العمارة" in text or "عمارة" in text:
        building["type"] = "building"

    for word, normalized_color in BUILDING_COLORS.items():
        if word in text:
            building["color"] = normalized_color
            break

    number_match = re.search(
        r"(?:بيت|البيت|عمارة|العمارة)\s+(?:رقم\s*)?(\d+)",
        text,
    )

    if number_match:
        building["number"] = number_match.group(1)

    floor_match = re.search(
        r"(?:الطابق|طابق)\s+(الأول|الاول|الثاني|الثالث|الرابع|\d+)",
        text,
    )

    if floor_match:
        building["floor"] = floor_match.group(1)

    return building


def parse_descriptive_address(raw_text: str) -> dict:
    text = normalize_arabic_address(raw_text)

    administrative_areas = detect_administrative_areas(text)
    landmarks = _extract_landmarks(text)

    # Prefer the most specific known administrative area
    area_scope = (
        administrative_areas.get("neighborhood")
        or administrative_areas.get("locality")
        or administrative_areas.get("city")
        or administrative_areas.get("governorate")
    )

    for landmark in landmarks:
        database_match = match_place(
            landmark_text=landmark["text"],
            area_name=area_scope,
        )

        if database_match:
            landmark["place_id"] = database_match["place_id"]
            landmark["matched_name"] = database_match["name_ar"]
            landmark["matched_by"] = database_match["matched_by"]
            landmark["match_score"] = database_match["match_score"]
            landmark["database_confidence"] = database_match["place_confidence"]
            landmark["matched_area"] = database_match["area_name"]
            landmark["latitude"] = database_match["latitude"]
            landmark["longitude"] = database_match["longitude"]
        else:
            landmark["place_id"] = None
            landmark["matched_name"] = None
            landmark["matched_by"] = None
            landmark["match_score"] = 0.0
            landmark["database_confidence"] = None
            landmark["matched_area"] = None
            landmark["latitude"] = None
            landmark["longitude"] = None

    directions = _extract_directions(text)
    distances = _extract_distances(text)
    building = _extract_building(text)

    detected_parts = 0

    if administrative_areas["city"]:
        detected_parts += 1

    if administrative_areas["locality"]:
        detected_parts += 1

    if landmarks:
        detected_parts += 1

    if directions:
        detected_parts += 1

    if any(building.values()):
        detected_parts += 1

    confidence = min(
        0.95,
        0.30 + (detected_parts * 0.12),
    )

    return {
        "administrative_areas": administrative_areas,
        "street": None,
        "landmarks": landmarks,
        "directions": directions,
        "building": building,
        "unresolved_terms": [],
        "overall_confidence": round(confidence, 2),
        "distances": distances,
    }
def _extract_distances(text: str) -> list[dict]:
    distances = []

    patterns = [
        r"(?:امشي|امش|سر|روح|كمل|بعدها)?\s*(\d+)\s*(?:متر|م)",
        r"(?:مسافة|حوالي)\s*(\d+)\s*(?:متر|م)",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            meters = int(match.group(1))

            distances.append(
                {
                    "instruction": "distance",
                    "meters": meters,
                    "raw_text": match.group(0).strip(),
                    "position": match.start(),
                    "confidence": 0.90,
                }
            )

    return distances
