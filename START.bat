@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title PRIZMBET - Auto Start

echo.
echo ===============================================================
echo.
echo            PRIZMBET - CRYPTO BOOKMAKER
echo.
echo ===============================================================
echo.
echo [*] Preparing to start...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo [*] Install Python from https://www.python.org/downloads/
    echo     Check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python found: 
python --version
echo.

REM Check dependencies
echo [*] Checking dependencies...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo.
    echo [*] Installing required libraries...
    echo.
    pip install -U requests beautifulsoup4 lxml schedule
    echo.
)

echo [OK] All dependencies installed
echo.

REM Check files
if not exist "marathon_to_sheets.py" (
    echo [ERROR] File marathon_to_sheets.py not found!
    pause
    exit /b 1
)

if not exist "auto_update_server.py" (
    echo [ERROR] File auto_update_server.py not found!
    pause
    exit /b 1
)

if not exist "index.html" (
    echo [ERROR] File index.html not found!
    pause
    exit /b 1
)

echo ===============================================================
echo.
echo Select mode:
echo.
echo   [1] Auto-update + Web server (recommended)
echo   [2] Auto-update only
echo   [3] Web server only
echo   [4] One-time update (test)
echo   [5] Exit
echo.
set /p choice="Enter number (1-5): "

if "%choice%"=="1" goto mode1
if "%choice%"=="2" goto mode2
if "%choice%"=="3" goto mode3
if "%choice%"=="4" goto mode4
if "%choice%"=="5" exit /b 0
echo.
echo [ERROR] Invalid choice!
pause
exit /b 1

:mode1
echo.
echo ===============================================================
echo   Starting: Auto-update + Web server
echo ===============================================================
echo.
echo [*] Starting auto-update...
start "PRIZMBET Auto-update" cmd /k python auto_update_server.py
timeout /t 3 /nobreak >nul
echo.
echo [*] Starting web server...
start "PRIZMBET Web server" cmd /k python -m http.server 8000
timeout /t 2 /nobreak >nul
echo.
echo [OK] Both services started!
echo.
echo [*] Open in browser: http://localhost:8000
echo.
timeout /t 3 /nobreak >nul
start http://localhost:8000
echo.
echo [*] Windows will remain open. Close them to stop servers.
echo.
pause
exit /b 0

:mode2
echo.
echo ===============================================================
echo   Starting: Auto-update only
echo ===============================================================
echo.
echo [*] Starting auto-update...
python auto_update_server.py
pause
exit /b 0

:mode3
echo.
echo ===============================================================
echo   Starting: Web server only
echo ===============================================================
echo.
echo [*] Starting web server on port 8000...
echo.
echo [*] Open in browser: http://localhost:8000
echo.
timeout /t 2 /nobreak >nul
start http://localhost:8000
echo.
python -m http.server 8000
pause
exit /b 0

:mode4
echo.
echo ===============================================================
echo   Test update
echo ===============================================================
echo.
echo [*] Starting parser...
echo.
python marathon_to_sheets.py
echo.
if exist "matches.json" (
    echo [OK] File matches.json created successfully!
    echo.
    for %%I in (matches.json) do echo [*] File size: %%~zI bytes
    echo.
) else (
    echo [ERROR] File matches.json not created
    echo.
)
pause
exit /b 0
