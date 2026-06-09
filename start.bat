@echo off

REM TODO: Include runtime env setup (uv + python etc.)

REM =====================================================
REM BOOTSTRAP SCRIPT: START.BAT
REM Purpose: Determines the dedicated data path and launches the Python application.
REM =====================================================

SETLOCAL

REM --- 1. Configuration ---
set APP_NAME=finance-agent

REM --- 2. Determine the System Path (User-specific data location) ---
REM %LOCALAPPDATA% is the robust, machine-independent path.
set DATA_PATH=%LOCALAPPDATA%\%APP_NAME%

REM --- 3. Ensure the Directory Exists ---
mkdir "%DATA_PATH%" 2>nul

REM --- 4. Execution ---
python main.py --data-dir "%DATA_PATH%"

ENDLOCAL
