from sqlalchemy import text

from app.db.session import SessionLocal


def match_place(
    landmark_text: str,
    area_name: str | None = None,
) -> dict | None:
    """
    Match a parsed landmark against the Palestinian places knowledge base.

    Matching priority:
    1. Official place name
    2. Place aliases
    3. Fuzzy similarity using PostgreSQL pg_trgm

    Optionally scopes the search to an administrative area.
    """

    query = text(
        """
        WITH candidates AS (

            SELECT
                p.id AS place_id,
                p.name_ar,
                p.name_en,
                p.place_type,
                p.confidence AS place_confidence,
                a.name_ar AS area_name,

                ST_Y(p.geom) AS latitude,
                ST_X(p.geom) AS longitude,

                p.normalized_name_ar AS matched_text,

                CASE
                    WHEN p.normalized_name_ar = :landmark_text
                        THEN 1.0
                    ELSE similarity(
                        p.normalized_name_ar,
                        :landmark_text
                    )
                END AS match_score,

                'official_name' AS matched_by

            FROM places p

            LEFT JOIN administrative_areas a
                ON a.id = p.administrative_area_id

            WHERE
                (
                    CAST(:area_name AS TEXT) IS NULL
                    OR a.name_ar = CAST(:area_name AS TEXT)
                )
                AND (
                    p.normalized_name_ar = :landmark_text
                    OR similarity(
                        p.normalized_name_ar,
                        :landmark_text
                    ) >= 0.35
                )


            UNION ALL


            SELECT
                p.id AS place_id,
                p.name_ar,
                p.name_en,
                p.place_type,
                p.confidence AS place_confidence,
                a.name_ar AS area_name,

                ST_Y(p.geom) AS latitude,
                ST_X(p.geom) AS longitude,

                pa.normalized_alias AS matched_text,

                CASE
                    WHEN pa.normalized_alias = :landmark_text
                        THEN 1.0
                    ELSE similarity(
                        pa.normalized_alias,
                        :landmark_text
                    )
                END AS match_score,

                'alias' AS matched_by

            FROM place_aliases pa

            JOIN places p
                ON p.id = pa.place_id

            LEFT JOIN administrative_areas a
                ON a.id = p.administrative_area_id

            WHERE
                (
                    CAST(:area_name AS TEXT) IS NULL
                    OR a.name_ar = CAST(:area_name AS TEXT)
                )
                AND (
                    pa.normalized_alias = :landmark_text
                    OR similarity(
                        pa.normalized_alias,
                        :landmark_text
                    ) >= 0.35
                )
        )

        SELECT
            place_id,
            name_ar,
            name_en,
            place_type,
            area_name,
            latitude,
            longitude,
            matched_text,
            match_score,
            place_confidence,
            matched_by

        FROM candidates

        ORDER BY
            match_score DESC,
            place_confidence DESC

        LIMIT 1;
        """
    )

    with SessionLocal() as db:
        row = db.execute(
            query,
            {
                "landmark_text": landmark_text,
                "area_name": area_name,
            },
        ).mappings().first()

    if row is None:
        return None

    return {
        "place_id": row["place_id"],
        "name_ar": row["name_ar"],
        "name_en": row["name_en"],
        "place_type": row["place_type"],
        "area_name": row["area_name"],
        "latitude": float(row["latitude"]) if row["latitude"] is not None else None,
        "longitude": float(row["longitude"]) if row["longitude"] is not None else None,
        "matched_text": row["matched_text"],
        "match_score": float(row["match_score"]),
        "place_confidence": float(row["place_confidence"]),
        "matched_by": row["matched_by"],
    }
