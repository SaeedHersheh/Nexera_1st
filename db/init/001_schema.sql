CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TYPE administrative_area_type AS ENUM (
    'country',
    'governorate',
    'city',
    'town',
    'village',
    'camp',
    'neighborhood',
    'locality',
    'other'
);

CREATE TYPE verification_method AS ENUM (
    'USER_CONFIRMATION',
    'DRIVER_CONFIRMATION',
    'DELIVERY_SUCCESS',
    'MANUAL',
    'ADMIN',
    'IMPORT'
);

CREATE TABLE administrative_areas (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT REFERENCES administrative_areas(id) ON DELETE SET NULL,

    name_ar TEXT NOT NULL,
    name_en TEXT,
    normalized_name_ar TEXT NOT NULL,
    area_type administrative_area_type NOT NULL,

    geom geometry(MultiPolygon, 4326),

    source TEXT,
    source_reference TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_administrative_areas_parent
    ON administrative_areas(parent_id);

CREATE INDEX idx_administrative_areas_name_trgm
    ON administrative_areas
    USING GIN (normalized_name_ar gin_trgm_ops);

CREATE INDEX idx_administrative_areas_geom
    ON administrative_areas
    USING GIST (geom);


CREATE TABLE places (
    id BIGSERIAL PRIMARY KEY,
    administrative_area_id BIGINT
        REFERENCES administrative_areas(id) ON DELETE SET NULL,

    name_ar TEXT NOT NULL,
    name_en TEXT,
    normalized_name_ar TEXT NOT NULL,

    place_type TEXT NOT NULL,

    location geography(Point, 4326),
    geom geometry(Point, 4326),

    source TEXT,
    source_reference TEXT,

    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000
        CHECK (confidence >= 0 AND confidence <= 1),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_places_area
    ON places(administrative_area_id);

CREATE INDEX idx_places_type
    ON places(place_type);

CREATE INDEX idx_places_name_trgm
    ON places
    USING GIN (normalized_name_ar gin_trgm_ops);

CREATE INDEX idx_places_location
    ON places
    USING GIST (location);

CREATE INDEX idx_places_geom
    ON places
    USING GIST (geom);


CREATE TABLE place_aliases (
    id BIGSERIAL PRIMARY KEY,
    place_id BIGINT NOT NULL
        REFERENCES places(id) ON DELETE CASCADE,

    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,

    language_code VARCHAR(10) NOT NULL DEFAULT 'ar',
    dialect TEXT DEFAULT 'palestinian',

    source TEXT,
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000
        CHECK (confidence >= 0 AND confidence <= 1),

    usage_count BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(place_id, normalized_alias)
);

CREATE INDEX idx_place_aliases_place
    ON place_aliases(place_id);

CREATE INDEX idx_place_aliases_trgm
    ON place_aliases
    USING GIN (normalized_alias gin_trgm_ops);


CREATE TABLE streets (
    id BIGSERIAL PRIMARY KEY,
    administrative_area_id BIGINT
        REFERENCES administrative_areas(id) ON DELETE SET NULL,

    name_ar TEXT NOT NULL,
    name_en TEXT,
    normalized_name_ar TEXT NOT NULL,

    geom geometry(MultiLineString, 4326),

    source TEXT,
    source_reference TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_streets_area
    ON streets(administrative_area_id);

CREATE INDEX idx_streets_name_trgm
    ON streets
    USING GIN (normalized_name_ar gin_trgm_ops);

CREATE INDEX idx_streets_geom
    ON streets
    USING GIST (geom);


CREATE TABLE street_aliases (
    id BIGSERIAL PRIMARY KEY,
    street_id BIGINT NOT NULL
        REFERENCES streets(id) ON DELETE CASCADE,

    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,

    source TEXT,
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000
        CHECK (confidence >= 0 AND confidence <= 1),

    usage_count BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(street_id, normalized_alias)
);

CREATE INDEX idx_street_aliases_trgm
    ON street_aliases
    USING GIN (normalized_alias gin_trgm_ops);


CREATE TABLE raw_addresses (
    id BIGSERIAL PRIMARY KEY,

    raw_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,

    language_code VARCHAR(10) NOT NULL DEFAULT 'ar',
    source TEXT,

    client_context JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_raw_addresses_text_trgm
    ON raw_addresses
    USING GIN (normalized_text gin_trgm_ops);


CREATE TABLE parsing_runs (
    id BIGSERIAL PRIMARY KEY,
    raw_address_id BIGINT NOT NULL
        REFERENCES raw_addresses(id) ON DELETE CASCADE,

    parser_version TEXT NOT NULL,
    model_name TEXT,

    parsed_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    confidence NUMERIC(5,4)
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),

    processing_time_ms INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_parsing_runs_raw
    ON parsing_runs(raw_address_id);

CREATE INDEX idx_parsing_runs_json
    ON parsing_runs
    USING GIN (parsed_json);


CREATE TABLE parsed_entities (
    id BIGSERIAL PRIMARY KEY,
    parsing_run_id BIGINT NOT NULL
        REFERENCES parsing_runs(id) ON DELETE CASCADE,

    entity_type TEXT NOT NULL,

    original_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,

    start_position INTEGER,
    end_position INTEGER,

    confidence NUMERIC(5,4)
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),

    matched_place_id BIGINT
        REFERENCES places(id) ON DELETE SET NULL,

    matched_street_id BIGINT
        REFERENCES streets(id) ON DELETE SET NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_parsed_entities_run
    ON parsed_entities(parsing_run_id);

CREATE INDEX idx_parsed_entities_type
    ON parsed_entities(entity_type);


CREATE TABLE address_relations (
    id BIGSERIAL PRIMARY KEY,
    parsing_run_id BIGINT NOT NULL
        REFERENCES parsing_runs(id) ON DELETE CASCADE,

    relation_type TEXT NOT NULL,

    source_entity_id BIGINT
        REFERENCES parsed_entities(id) ON DELETE SET NULL,

    target_entity_id BIGINT
        REFERENCES parsed_entities(id) ON DELETE SET NULL,

    raw_relation_text TEXT,

    numeric_value NUMERIC,
    unit TEXT,

    confidence NUMERIC(5,4)
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_address_relations_run
    ON address_relations(parsing_run_id);


CREATE TABLE address_candidates (
    id BIGSERIAL PRIMARY KEY,
    raw_address_id BIGINT NOT NULL
        REFERENCES raw_addresses(id) ON DELETE CASCADE,

    parsing_run_id BIGINT
        REFERENCES parsing_runs(id) ON DELETE SET NULL,

    location geography(Point, 4326) NOT NULL,

    rank INTEGER NOT NULL,

    overall_score NUMERIC(5,4) NOT NULL
        CHECK (overall_score >= 0 AND overall_score <= 1),

    nlp_score NUMERIC(5,4),
    landmark_score NUMERIC(5,4),
    spatial_score NUMERIC(5,4),
    context_score NUMERIC(5,4),

    explanation JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_address_candidates_raw
    ON address_candidates(raw_address_id);

CREATE INDEX idx_address_candidates_location
    ON address_candidates
    USING GIST (location);


CREATE TABLE verified_addresses (
    id BIGSERIAL PRIMARY KEY,
    raw_address_id BIGINT NOT NULL
        REFERENCES raw_addresses(id) ON DELETE CASCADE,

    candidate_id BIGINT
        REFERENCES address_candidates(id) ON DELETE SET NULL,

    location geography(Point, 4326) NOT NULL,

    verification_method verification_method NOT NULL,

    verifier_reference TEXT,

    confidence NUMERIC(5,4) NOT NULL DEFAULT 1.0000
        CHECK (confidence >= 0 AND confidence <= 1),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_verified_addresses_raw
    ON verified_addresses(raw_address_id);

CREATE INDEX idx_verified_addresses_location
    ON verified_addresses
    USING GIST (location);


CREATE TABLE address_feedback (
    id BIGSERIAL PRIMARY KEY,
    raw_address_id BIGINT NOT NULL
        REFERENCES raw_addresses(id) ON DELETE CASCADE,

    candidate_id BIGINT
        REFERENCES address_candidates(id) ON DELETE SET NULL,

    feedback_type TEXT NOT NULL,

    suggested_location geography(Point, 4326),
    correct_location geography(Point, 4326),

    notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_address_feedback_raw
    ON address_feedback(raw_address_id);


CREATE TABLE schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO schema_meta(key, value)
VALUES ('schema_version', '0.1.0')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
