@echo off
title AgTools Professional
echo.
echo ====================================================
echo   AgTools Professional - Crop Consulting System
echo ====================================================
echo.

cd /d "%~dp0"

echo Starting backend server...
start /B /MIN cmd /c "cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting desktop application...
cd frontend
python main.py

echo.
echo Shutting down backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq AgTools*" >nul 2>&1

echo AgTools closed.
