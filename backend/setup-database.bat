@echo off
REM PostgreSQL Database Setup for FloatChat Ultimate
REM This script will create the database and user

echo ========================================
echo FloatChat Ultimate - Database Setup
echo ========================================
echo.
echo This script will:
echo 1. Create floatchat_user
echo 2. Create floatchat database
echo 3. Run init-db.sql (create tables)
echo 4. Run db-enhancements.sql (indexes, views)
echo.
echo You will be prompted for the PostgreSQL postgres user password
echo (the password you set during PostgreSQL installation)
echo.
pause

set PGPATH="C:\Program Files\PostgreSQL\17\bin\psql.exe"
set PGUSER=postgres

echo.
echo Step 1: Creating user floatchat_user...
%PGPATH% -U %PGUSER% -c "CREATE USER floatchat_user WITH PASSWORD 'floatchat_password_dev';"

echo.
echo Step 2: Creating database floatchat...
%PGPATH% -U %PGUSER% -c "CREATE DATABASE floatchat OWNER floatchat_user;"

echo.
echo Step 3: Granting privileges...
%PGPATH% -U %PGUSER% -d floatchat -c "GRANT ALL ON SCHEMA public TO floatchat_user;"
%PGPATH% -U %PGUSER% -d floatchat -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO floatchat_user;"
%PGPATH% -U %PGUSER% -d floatchat -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO floatchat_user;"

echo.
echo Step 4: Running init-db.sql...
%PGPATH% -U floatchat_user -d floatchat -f init-db.sql

echo.
echo Step 5: Running db-enhancements.sql...
%PGPATH% -U floatchat_user -d floatchat -f db-enhancements.sql

echo.
echo ========================================
echo Database setup complete!
echo ========================================
echo.
echo Database: floatchat
echo User: floatchat_user
echo Password: floatchat_password_dev
echo.
echo You can now start the backend with PostgreSQL!
echo.
pause
