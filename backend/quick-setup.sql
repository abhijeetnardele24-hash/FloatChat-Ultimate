-- Simple database setup script
-- Run this with: psql -U postgres -f quick-setup.sql

-- Create user (ignore error if exists)
DO $$
BEGIN
    CREATE USER floatchat_user WITH PASSWORD 'floatchat_password_dev';
EXCEPTION WHEN duplicate_object THEN
    RAISE NOTICE 'User floatchat_user already exists';
END$$;

-- Create database (ignore error if exists)
SELECT 'CREATE DATABASE floatchat OWNER floatchat_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'floatchat')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE floatchat TO floatchat_user;

\c floatchat

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO floatchat_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO floatchat_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO floatchat_user;

\echo 'Database setup complete! Now run init-db.sql and db-enhancements.sql'
