CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS cameras (
    osm_id BIGINT PRIMARY KEY,
    location GEOMETRY(Point, 4326) NOT NULL,
    surveillance_type VARCHAR(50),
    camera_direction INTEGER,
    camera_type VARCHAR(50),
    operator VARCHAR(255),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS cameras_location_idx ON cameras USING GIST (location);
CREATE INDEX IF NOT EXISTS cameras_type_idx ON cameras (surveillance_type);

CREATE TABLE IF NOT EXISTS sync_log (
    id SERIAL PRIMARY KEY,
    region VARCHAR(100),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cameras_found INTEGER,
    cameras_updated INTEGER,
    status VARCHAR(20)
);
