from sqlalchemy import text

from app.db.session import SessionLocal


AREA_TYPE_MAP = {
    "governorate": "governorate",
    "city": "city",
    "town": "locality",
    "village": "locality",
    "camp": "locality",
    "locality": "locality",
    "neighborhood": "neighborhood",
}


def detect_administrative_areas(address_text: str) -> dict:
    """
    Detect administrative areas from PostgreSQL.

    The parser no longer needs hard-coded city/locality lists.
    Adding a new place to administrative_areas is enough for
    the system to recognize it.
    """

    result = {
        "governorate": None,
        "city": None,
        "locality": None,
        "neighborhood": None,
    }

    query = text(
        """
        SELECT
            id,
            name_ar,
            normalized_name_ar,
            area_type,
            parent_id
        FROM administrative_areas
        WHERE area_type <> 'country'
          AND POSITION(normalized_name_ar IN :address_text) > 0
        ORDER BY
            LENGTH(normalized_name_ar) DESC,
            CASE area_type
                WHEN 'neighborhood' THEN 1
                WHEN 'locality' THEN 2
                WHEN 'village' THEN 3
                WHEN 'town' THEN 4
                WHEN 'city' THEN 5
                WHEN 'governorate' THEN 6
                ELSE 10
            END
        """
    )

    with SessionLocal() as db:
        rows = db.execute(
            query,
            {"address_text": address_text},
        ).mappings().all()

    for row in rows:
        target_key = AREA_TYPE_MAP.get(row["area_type"])

        if target_key and result[target_key] is None:
            result[target_key] = row["name_ar"]

    return result
