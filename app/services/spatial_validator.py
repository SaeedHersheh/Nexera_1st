from __future__ import annotations

from sqlalchemy import text

from app.db.session import SessionLocal
from app.nlp.normalizer import normalize_arabic_address


RELATION_MAX_DISTANCE = {
    "at": 25,
    "next_to": 50,
    "opposite": 70,
    "near": 200,

    # These are mainly navigation relations,
    # not pure radius relations.
    "after": 250,
    "before": 250,
    "behind": 80,
    "in_front_of": 80,
}


class SpatialValidator:
    def find_nearby_pois(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 200,
        area_name: str | None = None,
        limit: int = 25,
    ) -> list[dict]:

        query = text(
            """
            SELECT
                p.id,
                p.name_ar,
                p.name_en,
                p.place_type,
                a.name_ar AS area_name,

                ST_Y(p.geom) AS latitude,
                ST_X(p.geom) AS longitude,

                ST_Distance(
                    p.geom::geography,
                    ST_SetSRID(
                        ST_MakePoint(
                            :longitude,
                            :latitude
                        ),
                        4326
                    )::geography
                ) AS distance_m

            FROM places p

            LEFT JOIN administrative_areas a
                ON a.id = p.administrative_area_id

            WHERE
                p.geom IS NOT NULL

                AND ST_DWithin(
                    p.geom::geography,
                    ST_SetSRID(
                        ST_MakePoint(
                            :longitude,
                            :latitude
                        ),
                        4326
                    )::geography,
                    :radius
                )

                AND (
                    CAST(:area_name AS TEXT) IS NULL
                    OR a.name_ar = CAST(:area_name AS TEXT)
                )

            ORDER BY distance_m ASC

            LIMIT :limit
            """
        )

        with SessionLocal() as db:
            rows = db.execute(
                query,
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius": radius_meters,
                    "area_name": area_name,
                    "limit": limit,
                },
            ).mappings().all()

        return [
            {
                "place_id": row["id"],
                "name_ar": row["name_ar"],
                "name_en": row["name_en"],
                "place_type": row["place_type"],
                "area_name": row["area_name"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "distance_m": round(
                    float(row["distance_m"]),
                    2,
                ),
            }
            for row in rows
        ]

    def validate_landmark(
        self,
        expected_text: str,
        latitude: float,
        longitude: float,
        relation: str | None = None,
        radius_meters: float | None = None,
        area_name: str | None = None,
        expected_type: str | None = None,
    ) -> dict:

        expected_normalized = normalize_arabic_address(
            expected_text
        )

        # Relation controls the allowed radius.
        relation_radius = RELATION_MAX_DISTANCE.get(
            relation,
            200,
        )

        if radius_meters is None:
            radius_meters = relation_radius

        query = text(
            """
            SELECT
                p.id,
                p.name_ar,
                p.name_en,
                p.place_type,
                a.name_ar AS area_name,

                ST_Y(p.geom) AS latitude,
                ST_X(p.geom) AS longitude,

                similarity(
                    p.normalized_name_ar,
                    :expected_text
                ) AS name_similarity,

                ST_Distance(
                    p.geom::geography,
                    ST_SetSRID(
                        ST_MakePoint(
                            :longitude,
                            :latitude
                        ),
                        4326
                    )::geography
                ) AS distance_m

            FROM places p

            LEFT JOIN administrative_areas a
                ON a.id = p.administrative_area_id

            WHERE
                p.geom IS NOT NULL

                AND ST_DWithin(
                    p.geom::geography,
                    ST_SetSRID(
                        ST_MakePoint(
                            :longitude,
                            :latitude
                        ),
                        4326
                    )::geography,
                    :radius
                )

                AND (
                    CAST(:area_name AS TEXT) IS NULL
                    OR a.name_ar = CAST(:area_name AS TEXT)
                )

            ORDER BY
                similarity(
                    p.normalized_name_ar,
                    :expected_text
                ) DESC,
                distance_m ASC

            LIMIT 10
            """
        )

        with SessionLocal() as db:
            rows = db.execute(
                query,
                {
                    "expected_text": expected_normalized,
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius": radius_meters,
                    "area_name": area_name,
                },
            ).mappings().all()

        candidates = []

        for row in rows:
            distance = float(
                row["distance_m"]
            )

            name_similarity = float(
                row["name_similarity"]
            )

            proximity_score = max(
                0.0,
                1.0 - (
                    distance / radius_meters
                ),
            )

            type_score = 0.0

            if expected_type:
                if row["place_type"] == expected_type:
                    type_score = 1.0

            final_score = (
                name_similarity * 0.70
                + proximity_score * 0.20
                + type_score * 0.10
            )

            candidates.append(
                {
                    "place_id": row["id"],
                    "name_ar": row["name_ar"],
                    "place_type": row["place_type"],
                    "area_name": row["area_name"],

                    "latitude": float(
                        row["latitude"]
                    ),

                    "longitude": float(
                        row["longitude"]
                    ),

                    "distance_m": round(
                        distance,
                        2,
                    ),

                    "name_similarity": round(
                        name_similarity,
                        3,
                    ),

                    "proximity_score": round(
                        proximity_score,
                        3,
                    ),

                    "validation_score": round(
                        final_score,
                        3,
                    ),
                }
            )

        candidates.sort(
            key=lambda item: (
                -item["validation_score"],
                item["distance_m"],
            )
        )

        best = (
            candidates[0]
            if candidates
            else None
        )

        matched = (
            best is not None
            and best["name_similarity"] >= 0.35
            and best["distance_m"] <= relation_radius
        )

        return {
            "expected_landmark": expected_text,
            "relation": relation,

            "relation_max_distance_m": (
                relation_radius
            ),

            "search_radius_m": (
                radius_meters
            ),

            "matched": matched,
            "best_match": best,
            "candidates": candidates,
        }
