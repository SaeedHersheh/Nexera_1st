-- Confirm PostGIS is enabled
SELECT PostGIS_Version();

-- Count tables in public schema
SELECT COUNT(*)
FROM information_schema.tables
WHERE table_schema = 'public';

-- Example: nearest verified places within 1km.
-- Replace longitude/latitude with real values.
SELECT
    id,
    name_ar,
    place_type,
    ST_Distance(
        location,
        ST_SetSRID(ST_MakePoint(35.0, 32.0), 4326)::geography
    ) AS distance_meters
FROM places
WHERE location IS NOT NULL
  AND ST_DWithin(
      location,
      ST_SetSRID(ST_MakePoint(35.0, 32.0), 4326)::geography,
      1000
  )
ORDER BY distance_meters
LIMIT 20;
