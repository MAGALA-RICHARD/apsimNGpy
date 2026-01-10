@echo off
REM Usage:
REM   setup_venv.bat          -> setup, install, run scripts, then exit
REM   setup_venv.bat shell    -> setup, install, run scripts, then open an ACTIVATED CMD

REM --- Ensure Python is available ---
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found on PATH.
  pause
  exit /b 1
)

REM --- Create venv with pinned Python version ---
if not exist ".venv" (
  echo [INFO] Creating virtual environment with Python 3.12 ...
  uv venv .venv --python 3.13
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
  )
)


REM --- Activate venv (CMD) ---
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  pause
  exit /b 1
)

REM --- Install requirements ---
if exist "requirements.txt" (
  echo [INFO] Installing from requirements.txt ...
  uv pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
  )
) else (
  echo [WARN] requirements.txt not found in %cd%.
)

REM --- Run scripts in order ---
for %%S in (./sens.py) do (
  if exist "%%S" (
    echo [RUN] python %%S
    python "%%S"
    if errorlevel 1 (
      echo [ERROR] Script %%S failed. Aborting.
      pause
      exit /b 1
    )
  ) else (
    echo [WARN] Missing script %%S
  )
)

@echo off

REM --- Open an activated CMD that stays open
if /i "%~1"=="shell" (
    echo [OK] Opening an activated shell.
    echo.

    cmd /k call ".venv\Scripts\activate.bat"
    goto :eof
)

echo [OK] Done.
echo.

REM --- Ask user whether to close
set /p CLOSE_SHELL="Do you want to close this window? (Y/N): "

if /i "%CLOSE_SHELL%"=="Y" (
    exit /b 0
)

echo [INFO] Shell will remain open.
cmd /k

