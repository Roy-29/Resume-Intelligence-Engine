@echo off
echo ===============================================
echo   RecruitPro - Production Startup Script
echo ===============================================
echo.

REM 1. Start Redis (portable)
echo [1/3] Starting Redis server...
start "Redis Server" /MIN "d:\antigravity cv\redis\redis-server.exe"
timeout /t 2 /nobreak >nul

REM 2. Start Celery Worker (background task processor)
echo [2/3] Starting Celery worker...
start "Celery Worker" /MIN cmd /c "cd /d \"d:\antigravity cv\" && .venv\Scripts\celery.exe -A recruitment worker --loglevel=info --pool=solo"
timeout /t 3 /nobreak >nul

REM 3. Start Django (Daphne ASGI server)
echo [3/3] Starting Django server (Daphne)...
cd /d "d:\antigravity cv"
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

pause
