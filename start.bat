@echo off
REM =====================================================
REM BOOTSTRAP SCRIPT: START.BAT (Condensed Version)
REM Purpose: Determines the dedicated data path and launches the Python application.
REM =====================================================

SETLOCAL

REM --- 1. Configuration ---
set APP_NAME=finance-agent

REM --- 2. Determine the System Path (User-specific data location) ---
REM %LOCALAPPDATA% is the robust, machine-independent path.
set DATA_PATH=%LOCALAPPDATA%\%APP_NAME%

REM --- 3. Ensure the Directory Exists ---
REM /p flag ensures parent directories are also created.
REM 2>nul suppresses the error message if the directory already exists.
mkdir "%DATA_PATH%" 2>nul

REM --- 4. Execution ---
echo Running My Tool...
echo Data Path: %DATA_PATH%
echo ---------------------------------------------------

REM Pass the absolute path determined in step 2 as an argument.
python main.py --data-dir "%DATA_PATH%"

ENDLOCAL
