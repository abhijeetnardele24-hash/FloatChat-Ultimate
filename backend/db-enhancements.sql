-- Enhanced Database Schema with Indexes and Materialized Views
-- Run this after init-db.sql to add optimizations

-- Add PostGIS geography column to floats for spatial queries
ALTER TABLE argo_floats 
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(POINT, 4326);

-- Update location column from lat/lon
UPDATE argo_floats 
SET location = ST_SetSRID(ST_MakePoint(last_longitude, last_latitude), 4326)::geography
WHERE last_longitude IS NOT NULL AND last_latitude IS NOT NULL;

-- Add PostGIS geography column to profiles
ALTER TABLE argo_profiles 
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(POINT, 4326);

-- Update profile locations
UPDATE argo_profiles 
SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE longitude IS NOT NULL AND latitude IS NOT NULL;

-- Enhanced indexes for floats
CREATE INDEX IF NOT EXISTS idx_floats_location_gist 
ON argo_floats USING GIST(location);

CREATE INDEX IF NOT EXISTS idx_floats_status 
ON argo_floats(status) WHERE status IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_floats_ocean_basin 
ON argo_floats(ocean_basin) WHERE ocean_basin IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_floats_wmo 
ON argo_floats(wmo_number);

CREATE INDEX IF NOT EXISTS idx_floats_last_location_date 
ON argo_floats(last_location_date DESC) WHERE last_location_date IS NOT NULL;

-- Enhanced indexes for profiles
CREATE INDEX IF NOT EXISTS idx_profiles_location_gist 
ON argo_profiles USING GIST(location);

CREATE INDEX IF NOT EXISTS idx_profiles_wmo_cycle 
ON argo_profiles(wmo_number, cycle_number);

CREATE INDEX IF NOT EXISTS idx_profiles_wmo_date 
ON argo_profiles(wmo_number, profile_date DESC);

CREATE INDEX IF NOT EXISTS idx_profiles_float_id 
ON argo_profiles(float_id);

-- Enhanced indexes for measurements
CREATE INDEX IF NOT EXISTS idx_measurements_profile_id 
ON argo_measurements(profile_id);

CREATE INDEX IF NOT EXISTS idx_measurements_depth 
ON argo_measurements(depth) WHERE depth IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_measurements_temp 
ON argo_measurements(temperature) WHERE temperature IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_measurements_salinity 
ON argo_measurements(salinity) WHERE salinity IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_measurements_qc 
ON argo_measurements(temperature_qc, salinity_qc);

-- Materialized view for quick stats
CREATE MATERIALIZED VIEW IF NOT EXISTS argo_stats AS
SELECT 
    COUNT(DISTINCT f.wmo_number) as total_floats,
    COUNT(DISTINCT CASE WHEN f.status = 'ACTIVE' THEN f.wmo_number END) as active_floats,
    COUNT(DISTINCT CASE WHEN f.status = 'INACTIVE' THEN f.wmo_number END) as inactive_floats,
    COUNT(DISTINCT p.id) as total_profiles,
    MIN(p.profile_date) as earliest_profile,
    MAX(p.profile_date) as latest_profile,
    COUNT(DISTINCT f.ocean_basin) as ocean_basin_count,
    COUNT(DISTINCT m.id) as total_measurements,
    AVG(m.temperature) FILTER (WHERE m.temperature_qc <= 2) as avg_temperature,
    AVG(m.salinity) FILTER (WHERE m.salinity_qc <= 2) as avg_salinity
FROM argo_floats f
LEFT JOIN argo_profiles p ON f.id = p.float_id
LEFT JOIN argo_measurements m ON p.id = m.profile_id;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX ON argo_stats ((true));

-- Materialized view for ocean basin stats
CREATE MATERIALIZED VIEW IF NOT EXISTS argo_basin_stats AS
SELECT 
    ocean_basin,
    COUNT(DISTINCT wmo_number) as float_count,
    COUNT(DISTINCT CASE WHEN status = 'ACTIVE' THEN wmo_number END) as active_count,
    MIN(last_location_date) as earliest_data,
    MAX(last_location_date) as latest_data
FROM argo_floats
WHERE ocean_basin IS NOT NULL
GROUP BY ocean_basin;

-- Create index for basin stats
CREATE UNIQUE INDEX ON argo_basin_stats (ocean_basin);

-- Materialized view for recent profiles (last 30 days)
CREATE MATERIALIZED VIEW IF NOT EXISTS argo_recent_profiles AS
SELECT 
    p.id,
    p.wmo_number,
    p.cycle_number,
    p.profile_date,
    p.latitude,
    p.longitude,
    f.platform_type,
    f.status,
    f.ocean_basin,
    COUNT(m.id) as measurement_count
FROM argo_profiles p
JOIN argo_floats f ON p.float_id = f.id
LEFT JOIN argo_measurements m ON p.id = m.profile_id
WHERE p.profile_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY p.id, p.wmo_number, p.cycle_number, p.profile_date, p.latitude, p.longitude, 
         f.platform_type, f.status, f.ocean_basin
ORDER BY p.profile_date DESC;

-- Create index for recent profiles
CREATE UNIQUE INDEX ON argo_recent_profiles (id);
CREATE INDEX ON argo_recent_profiles (profile_date DESC);

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_argo_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY argo_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY argo_basin_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY argo_recent_profiles;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update location on insert/update for floats
CREATE OR REPLACE FUNCTION update_float_location()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.last_longitude IS NOT NULL AND NEW.last_latitude IS NOT NULL THEN
        NEW.location = ST_SetSRID(ST_MakePoint(NEW.last_longitude, NEW.last_latitude), 4326)::geography;
    END IF;
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_float_location
BEFORE INSERT OR UPDATE ON argo_floats
FOR EACH ROW
EXECUTE FUNCTION update_float_location();

-- Trigger to update location on insert/update for profiles
CREATE OR REPLACE FUNCTION update_profile_location()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL THEN
        NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_profile_location
BEFORE INSERT OR UPDATE ON argo_profiles
FOR EACH ROW
EXECUTE FUNCTION update_profile_location();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO floatchat_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO floatchat_user;
GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA public TO floatchat_user;

-- Refresh stats initially
SELECT refresh_argo_stats();

-- Comments for documentation
COMMENT ON MATERIALIZED VIEW argo_stats IS 'Platform-wide statistics refreshed periodically';
COMMENT ON MATERIALIZED VIEW argo_basin_stats IS 'Statistics grouped by ocean basin';
COMMENT ON MATERIALIZED VIEW argo_recent_profiles IS 'Profiles from the last 30 days with measurement counts';
COMMENT ON FUNCTION refresh_argo_stats() IS 'Refresh all materialized views concurrently';
