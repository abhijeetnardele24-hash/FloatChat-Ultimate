@echo off
REM FloatChat Ultimate - Backend Startup Script
REM Run this from anywhere: it switches to the backend folder first.

echo ========================================
echo FloatChat Ultimate Backend
echo ========================================
echo.

cd /d "%~dp0"

echo Current folder: %CD%
echo Setting environment variables...
set DATABASE_URL=postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat

echo.
echo Starting backend server on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo Press CTRL+C to stop.
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
