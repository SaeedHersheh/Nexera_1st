import csv
import hashlib
import json

from sqlalchemy import text

from app.db.session import SessionLocal
from app.nlp.normalizer import normalize_arabic_address


CSV_PATH = "data/jenin_pois_ready.csv"

AREA_ALIASES = {
    "Jenin City": "جنين",
}

SOURCE = "jenin_pois_csv"


def get_or_create_area(
    db,
    *,
    name_ar: str,
    area_type: str,
    parent_id: int,
    name_en: str | None = None,
) -> int:
    allowed_types = {
        "governorate",
        "city",
        "locality",
    }

    if area_type not in allowed_types:
        raise ValueError(
            f"Unsupported area type: {area_type}"
        )

    normalized = normalize_arabic_address(name_ar)

    existing = db.execute(
        text(
            f"""
            SELECT id
            FROM administrative_areas
            WHERE normalized_name_ar = :normalized
              AND area_type = '{area_type}'
              AND parent_id = :parent_id
            LIMIT 1
            """
        ),
        {
            "normalized": normalized,
            "parent_id": parent_id,
        },
    ).scalar()

    if existing:
        return existing

    area_id = db.execute(
        text(
            f"""
            INSERT INTO administrative_areas (
                parent_id,
                name_ar,
                name_en,
                normalized_name_ar,
                area_type,
                source,
                source_reference,
                is_verified,
                metadata
            )
            VALUES (
                :parent_id,
                :name_ar,
                :name_en,
                :normalized,
                '{area_type}',
                :source,
                :source_reference,
                FALSE,
                CAST(:metadata AS jsonb)
            )
            RETURNING id
            """
        ),
        {
            "parent_id": parent_id,
            "name_ar": name_ar,
            "name_en": name_en,
            "normalized": normalized,
            "source": SOURCE,
            "source_reference": f"jenin-area:{normalized}",
            "metadata": json.dumps(
                {
                    "import": "jenin_pois_ready.csv",
                },
                ensure_ascii=False,
            ),
        },
    ).scalar_one()

    return area_id


def make_source_reference(
    *,
    name: str,
    area: str,
    latitude: float,
    longitude: float,
) -> str:
    raw = (
        f"{normalize_arabic_address(name)}|"
        f"{normalize_arabic_address(area)}|"
        f"{latitude:.7f}|"
        f"{longitude:.7f}"
    )

    digest = hashlib.sha1(
        raw.encode("utf-8")
    ).hexdigest()

    return f"jenin-poi:{digest}"


def main():
    with open(
        CSV_PATH,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    print(f"CSV rows: {len(rows)}")

    with SessionLocal() as db:
        try:
            # -----------------------------
            # 1. Find Palestine
            # -----------------------------
            palestine_id = db.execute(
                text("""
                    SELECT id
                    FROM administrative_areas
                    WHERE area_type = 'country'
                      AND normalized_name_ar = 'فلسطين'
                    LIMIT 1
                """)
            ).scalar()

            if not palestine_id:
                raise RuntimeError(
                    "Palestine country record was not found."
                )

            # -----------------------------
            # 2. Jenin Governorate
            # -----------------------------
            jenin_governorate_id = get_or_create_area(
                db,
                name_ar="جنين",
                name_en="Jenin Governorate",
                area_type="governorate",
                parent_id=palestine_id,
            )

            # -----------------------------
            # 3. Jenin City
            # -----------------------------
            jenin_city_id = get_or_create_area(
                db,
                name_ar="جنين",
                name_en="Jenin",
                area_type="city",
                parent_id=jenin_governorate_id,
            )

            print(
                "Jenin Governorate ID:",
                jenin_governorate_id,
            )

            print(
                "Jenin City ID:",
                jenin_city_id,
            )

            # -----------------------------
            # 4. Create locality map
            # -----------------------------
            area_names = set()

            for row in rows:
                raw_area = row[
                    "sub_location"
                ].strip()

                if not raw_area:
                    continue

                area = AREA_ALIASES.get(
                    raw_area,
                    raw_area,
                )

                area_names.add(area)

            area_ids = {
                "جنين": jenin_city_id,
            }

            created_localities = 0

            for area in sorted(area_names):
                if area == "جنين":
                    continue

                area_id = get_or_create_area(
                    db,
                    name_ar=area,
                    area_type="locality",
                    parent_id=jenin_city_id,
                )

                area_ids[area] = area_id
                created_localities += 1

            print(
                "Localities available:",
                len(area_ids) - 1,
            )

            # -----------------------------
            # 5. Existing imported POIs
            # -----------------------------
            existing_refs = set(
                db.execute(
                    text("""
                        SELECT source_reference
                        FROM places
                        WHERE source = :source
                          AND source_reference IS NOT NULL
                    """),
                    {
                        "source": SOURCE,
                    },
                ).scalars().all()
            )

            # -----------------------------
            # 6. Find next place ID
            # -----------------------------
            next_place_id = db.execute(
                text("""
                    SELECT COALESCE(MAX(id), 0) + 1
                    FROM places
                """)
            ).scalar_one()

            inserts = []

            skipped_existing = 0
            skipped_invalid = 0

            for row in rows:
                name_ar = (
                    row.get("name_ar")
                    or row.get("display_name")
                    or row.get("poi_name")
                    or ""
                ).strip()

                if not name_ar:
                    skipped_invalid += 1
                    continue

                raw_area = (
                    row.get("sub_location")
                    or ""
                ).strip()

                area = AREA_ALIASES.get(
                    raw_area,
                    raw_area,
                )

                area_id = area_ids.get(area)

                if not area_id:
                    skipped_invalid += 1
                    continue

                try:
                    latitude = float(
                        row["latitude"]
                    )

                    longitude = float(
                        row["longitude"]
                    )
                except (
                    ValueError,
                    TypeError,
                ):
                    skipped_invalid += 1
                    continue

                if not (
                    -90 <= latitude <= 90
                    and
                    -180 <= longitude <= 180
                ):
                    skipped_invalid += 1
                    continue

                source_reference = (
                    make_source_reference(
                        name=name_ar,
                        area=area,
                        latitude=latitude,
                        longitude=longitude,
                    )
                )

                if source_reference in existing_refs:
                    skipped_existing += 1
                    continue

                name_en = (
                    row.get("name_en")
                    or ""
                ).strip() or None

                category = (
                    row.get("category")
                    or "unknown"
                ).strip()

                metadata = {
                    "city": row.get("city"),
                    "sub_location": raw_area,
                    "display_name": row.get(
                        "display_name"
                    ),
                    "poi_name": row.get(
                        "poi_name"
                    ),
                    "category": category,
                    "dist_to_center_m": (
                        row.get(
                            "dist_to_center_m"
                        )
                    ),
                    "import_file": (
                        "jenin_pois_ready.csv"
                    ),
                }

                inserts.append(
                    {
                        "id": next_place_id,
                        "administrative_area_id": (
                            area_id
                        ),
                        "name_ar": name_ar,
                        "name_en": name_en,
                        "normalized_name_ar": (
                            normalize_arabic_address(
                                name_ar
                            )
                        ),
                        "place_type": category,
                        "longitude": longitude,
                        "latitude": latitude,
                        "source": SOURCE,
                        "source_reference": (
                            source_reference
                        ),
                        "confidence": 0.90,
                        "metadata": json.dumps(
                            metadata,
                            ensure_ascii=False,
                        ),
                    }
                )

                existing_refs.add(
                    source_reference
                )

                next_place_id += 1

            # -----------------------------
            # 7. Bulk insert POIs
            # -----------------------------
            if inserts:
                db.execute(
                    text("""
                        INSERT INTO places (
                            id,
                            administrative_area_id,
                            name_ar,
                            name_en,
                            normalized_name_ar,
                            place_type,
                            geom,
                            source,
                            source_reference,
                            is_verified,
                            confidence,
                            metadata,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :id,
                            :administrative_area_id,
                            :name_ar,
                            :name_en,
                            :normalized_name_ar,
                            :place_type,

                            ST_SetSRID(
                                ST_MakePoint(
                                    :longitude,
                                    :latitude
                                ),
                                4326
                            ),

                            :source,
                            :source_reference,
                            FALSE,
                            :confidence,
                            CAST(:metadata AS jsonb),
                            NOW(),
                            NOW()
                        )
                    """),
                    inserts,
                )

            # -----------------------------
            # 8. Sync sequence if present
            # -----------------------------
            sequence_name = db.execute(
                text("""
                    SELECT pg_get_serial_sequence(
                        'places',
                        'id'
                    )
                """)
            ).scalar()

            if sequence_name:
                max_id = db.execute(
                    text("""
                        SELECT COALESCE(MAX(id), 1)
                        FROM places
                    """)
                ).scalar_one()

                db.execute(
                    text("""
                        SELECT setval(
                            CAST(:sequence_name AS regclass),
                            :max_id,
                            TRUE
                        )
                    """),
                    {
                        "sequence_name": (
                            sequence_name
                        ),
                        "max_id": max_id,
                    },
                )

            db.commit()

            print()
            print("=== IMPORT COMPLETE ===")
            print(
                "Inserted POIs:",
                len(inserts),
            )
            print(
                "Already existed:",
                skipped_existing,
            )
            print(
                "Invalid/skipped:",
                skipped_invalid,
            )

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
