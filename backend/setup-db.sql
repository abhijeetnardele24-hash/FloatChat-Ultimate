-- PostgreSQL Database Setup Script for FloatChat Ultimate
-- Run this script to create the database and user

-- Connect to postgres database first, then run these commands:

-- Create user
CREATE USER floatchat_user WITH PASSWORD 'floatchat_password_dev';

-- Create database
CREATE DATABASE floatchat OWNER floatchat_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE floatchat TO floatchat_user;

-- Connect to floatchat database and grant schema privileges
\c floatchat
GRANT ALL ON SCHEMA public TO floatchat_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO floatchat_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO floatchat_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO floatchat_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO floatchat_user;
