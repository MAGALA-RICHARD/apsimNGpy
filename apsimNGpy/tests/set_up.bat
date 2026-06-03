@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Usage:
REM   setup_venv.bat           -> setup, install, run tests, then exit
REM   setup_venv.bat shell     -> setup, install, run tests, then open an ACTIVATED CMD

set "VENV_DIR=.venv"
set "ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "TEST_FILE=apsimNGpy\tests\tester_main.py"

REM --- Ensure Python is available ---
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found on PATH.
  pause
  exit /b 1
)

REM --- Create venv if missing ---
if not exist "%VENV_DIR%" (
  echo [INFO] Creating virtual environment %VENV_DIR% ...
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
  )
)

REM --- Activate venv (CMD) ---
call "%ACTIVATE%"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  pause
  exit /b 1
)

REM --- Upgrade pip (quietly helpful) ---
python -m pip install --upgrade pip setuptools wheel >nul 2>nul

REM --- Install requirements if present; otherwise install apsimNGpy from GitHub ---
if exist "requirements.txt" (
  echo [INFO] Installing from requirements.txt ...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] pip install -r requirements.txt failed.
    pause
    exit /b 1
  )
) else (
  echo [WARN] requirements.txt not found. Installing apsimNGpy from GitHub ...
  where git >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Git not found on PATH (needed to fetch apsimNGpy).
    pause
    exit /b 1
  )
  python -m pip install "git+https://github.com/MAGALA-RICHARD/apsimNGpy.git"
  if errorlevel 1 (
    echo [ERROR] pip install of apsimNGpy failed.
    pause
    exit /b 1
  )
)

REM --- Ensure test file exists (clone only if needed) ---
if not exist "%TEST_FILE%" (
  echo [INFO] Local tests not found. Cloning apsimNGpy for tests ...
  where git >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Git not found on PATH (needed to clone tests).
    pause
    exit /b 1
  )
  git clone --depth 1 https://github.com/MAGALA-RICHARD/apsimNGpy.git
  if errorlevel 1 (
    echo [ERROR] git clone failed.
    pause
    exit /b 1
  )
)

REM --- Run tests/scripts in order ---
if exist "%TEST_FILE%" (
  echo [RUN] python "%TEST_FILE%"
  python "%TEST_FILE%"
  if errorlevel 1 (
    echo [ERROR] Test script failed. Aborting.
    pause
    exit /b 1
  )
) else (
  echo [WARN] Missing test script: %TEST_FILE%
)

REM --- Optionally open an ACTIVATED CMD that stays open ---
if /i "%~1"=="shell" (
  echo [OK] Opening an activated shell. Close it to exit.
  cmd /k call "%ACTIVATE%"
  exit /b 0
)

echo [OK] Done.
endlocal
