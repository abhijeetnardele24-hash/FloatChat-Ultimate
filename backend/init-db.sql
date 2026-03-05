-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ARGO floats table
CREATE TABLE IF NOT EXISTS argo_floats (
    id SERIAL PRIMARY KEY,
    wmo_number VARCHAR(20) UNIQUE NOT NULL,
    platform_type VARCHAR(50),
    deployment_date TIMESTAMP,
    last_location_date TIMESTAMP,
    last_latitude DOUBLE PRECISION,
    last_longitude DOUBLE PRECISION,
    status VARCHAR(20),
    program VARCHAR(100),
    ocean_basin VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index for float locations
CREATE INDEX IF NOT EXISTS idx_float_location 
ON argo_floats USING GIST (ST_MakePoint(last_longitude, last_latitude));

-- Create ARGO profiles table
CREATE TABLE IF NOT EXISTS argo_profiles (
    id SERIAL PRIMARY KEY,
    float_id INTEGER REFERENCES argo_floats(id) ON DELETE CASCADE,
    wmo_number VARCHAR(20) NOT NULL,
    cycle_number INTEGER NOT NULL,
    profile_date TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    position_qc INTEGER,
    data_mode CHAR(1),
    direction CHAR(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(wmo_number, cycle_number)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('argo_profiles', 'profile_date', 
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 month'
);

-- Create spatial index for profile locations
CREATE INDEX IF NOT EXISTS idx_profile_location 
ON argo_profiles USING GIST (ST_MakePoint(longitude, latitude));

-- Create time index
CREATE INDEX IF NOT EXISTS idx_profile_date 
ON argo_profiles (profile_date DESC);

-- Create ARGO measurements table
CREATE TABLE IF NOT EXISTS argo_measurements (
    id BIGSERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES argo_profiles(id) ON DELETE CASCADE,
    pressure DOUBLE PRECISION NOT NULL,
    depth DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    temperature_qc INTEGER,
    salinity DOUBLE PRECISION,
    salinity_qc INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on profile_id and pressure
CREATE INDEX IF NOT EXISTS idx_measurements_profile 
ON argo_measurements (profile_id, pressure);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sql_query TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user 
ON chat_sessions (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session 
ON chat_messages (session_id, created_at);

-- Insert sample data for testing
INSERT INTO argo_floats (wmo_number, platform_type, deployment_date, last_latitude, last_longitude, status, ocean_basin)
VALUES 
    ('2902756', 'APEX', '2020-01-15', 10.5, 75.2, 'ACTIVE', 'Indian Ocean'),
    ('2902834', 'ARVOR', '2019-06-20', 12.3, 78.5, 'ACTIVE', 'Indian Ocean'),
    ('2902912', 'APEX', '2021-03-10', 8.7, 72.1, 'ACTIVE', 'Indian Ocean')
ON CONFLICT (wmo_number) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO floatchat_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO floatchat_user;
