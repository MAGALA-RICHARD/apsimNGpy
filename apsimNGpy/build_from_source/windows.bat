@echo off
setlocal EnableExtensions EnableDelayedExpansion
title APSIM NG (ApsimX) - Local Build & Install (HERE)

REM ===================== CONFIG =====================
set "REPO_URL=https://github.com/APSIMInitiative/ApsimX.git"
set "CLONE_DIR=%CD%\ApsimX"
set "INSTALL_ROOT=%CD%\APSIMNG"
set "LOG=%CD%\install_apsimx.log"
set "TRY_PUBLISH=Y"          REM try dotnet publish if Models.exe not found
set "FORCE_RESTORE_BRANCH="  REM set to master or main if you want to force
REM ==================================================

echo > "%LOG%"
echo === APSIM NG installer (local) ===>>"%LOG%"
echo Working dir: %CD%>>"%LOG%"
echo Clone dir  : %CLONE_DIR%>>"%LOG%"
echo Install dir: %INSTALL_ROOT%>>"%LOG%"
echo. & echo [1/8] Checking prerequisites...
where git >nul 2>&1 || (echo [ERROR] Git not found in PATH. Install Git and re-run. & echo Git missing>>"%LOG%" & exit /b 1)
where dotnet >nul 2>&1 || (echo [ERROR] .NET SDK not found in PATH. Install the SDK and re-run. & echo .NET SDK missing>>"%LOG%" & exit /b 1)

echo Dotnet info (short)>>"%LOG%"
dotnet --list-sdks>>"%LOG%" 2>&1

echo. & echo [2/8] Getting source at "%CLONE_DIR%" ...
if exist "%CLONE_DIR%\.git" (
  echo   - Updating existing clone...
  pushd "%CLONE_DIR%" || (echo [ERROR] Cannot enter "%CLONE_DIR%". & goto :fail)
  git fetch --all --prune>>"%LOG%" 2>&1 || (echo [ERROR] git fetch failed. & goto :fail)
  if defined FORCE_RESTORE_BRANCH (
    git checkout %FORCE_RESTORE_BRANCH%>>"%LOG%" 2>&1 || (echo [ERROR] git checkout %FORCE_RESTORE_BRANCH% failed. & goto :fail)
  ) else (
    git checkout master>>"%LOG%" 2>&1 || git checkout main>>"%LOG%" 2>&1
  )
  git pull>>"%LOG%" 2>&1 || (echo [ERROR] git pull failed. & goto :fail)
) else (
  echo   - Cloning fresh repository...
  git clone "%REPO_URL%" "%CLONE_DIR%">>"%LOG%" 2>&1 || (echo [ERROR] git clone failed. See %LOG% & goto :fail)
  pushd "%CLONE_DIR%" || (echo [ERROR] Cannot enter "%CLONE_DIR%". & goto :fail)
  if defined FORCE_RESTORE_BRANCH (
    git checkout %FORCE_RESTORE_BRANCH%>>"%LOG%" 2>&1 || (echo [ERROR] git checkout %FORCE_RESTORE_BRANCH% failed. & goto :fail)
  ) else (
    git checkout master>>"%LOG%" 2>&1 || git checkout main>>"%LOG%" 2>&1
  )
)

echo. & echo [3/8] Restoring packages...
dotnet restore ApsimX.sln>>"%LOG%" 2>&1 || (echo [ERROR] dotnet restore failed. See %LOG% & goto :fail)

echo. & echo [4/8] Building solution (Release)...
dotnet build ApsimX.sln -c Release --nologo>>"%LOG%" 2>&1
if errorlevel 1 (
  echo   - Release build failed, trying Debug...
  dotnet build ApsimX.sln -c Debug --nologo>>"%LOG%" 2>&1 || (echo [ERROR] Build failed (Release & Debug). See %LOG% & goto :fail)
  set "BUILD_CONF=Debug"
) else (
  set "BUILD_CONF=Release"
)

echo. & echo [5/8] Searching for Models.exe ...
set "MODELS_DIR="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$m=Get-ChildItem -Recurse -File -Filter Models.exe | Sort-Object LastWriteTime -Desc | Select-Object -First 1 -ExpandProperty DirectoryName; $m"`) do set "MODELS_DIR=%%P"

if "%MODELS_DIR%"=="" (
  if /I "%TRY_PUBLISH%"=="Y" (
    echo   - Models.exe not found after build. Trying 'dotnet publish' for Models project...
    set "MODELS_PROJ="
    for /f "usebackq delims=" %%Q in (`powershell -NoProfile -Command "(Get-ChildItem -Recurse -File -Filter *.csproj | Where-Object { $_.BaseName -eq 'Models' } | Select-Object -First 1 -ExpandProperty FullName)"`) do set "MODELS_PROJ=%%Q"
    if "%MODELS_PROJ%"=="" (
      echo [ERROR] Could not find Models.csproj. See %LOG%
      goto :fail
    )
    set "PUB_OUT=%CLONE_DIR%\_publish\Models"
    dotnet publish "%MODELS_PROJ%" -c %BUILD_CONF% -r win-x64 --self-contained false -o "%PUB_OUT%">>"%LOG%" 2>&1 || (echo [ERROR] 'dotnet publish' failed. See %LOG% & goto :fail)
    if exist "%PUB_OUT%\Models.exe" (
      set "MODELS_DIR=%PUB_OUT%"
    )
  )
)

if "%MODELS_DIR%"=="" (
  echo [ERROR] Could not locate Models.exe after build/publish. See %LOG%
  goto :fail
)
echo   - Models.exe found in: %MODELS_DIR%
echo Found Models.exe at: %MODELS_DIR%>>"%LOG%"

echo. & echo [6/8] Installing locally to "%INSTALL_ROOT%" ...
mkdir "%INSTALL_ROOT%\Models" >nul 2>&1
mkdir "%INSTALL_ROOT%\UI" >nul 2>&1

robocopy "%MODELS_DIR%" "%INSTALL_ROOT%\Models" /MIR /NFL /NDL /NJH /NJS /NP>>"%LOG%" 2>&1
if errorlevel 8 (echo [ERROR] Copy of Models output failed. See %LOG% & goto :fail)

set "UI_DIR="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$u=Get-ChildItem -Recurse -File -Filter ApsimNG.exe | Sort-Object LastWriteTime -Desc | Select-Object -First 1 -ExpandProperty DirectoryName; $u"`) do set "UI_DIR=%%P"
if not "%UI_DIR%"=="" (
  robocopy "%UI_DIR%" "%INSTALL_ROOT%\UI" /MIR /NFL /NDL /NJH /NJS /NP>>"%LOG%" 2>&1
)

echo. & echo [7/8] Verifying install...
if not exist "%INSTALL_ROOT%\Models\Models.exe" (
  echo [ERROR] Verification failed: "%INSTALL_ROOT%\Models\Models.exe" not found.
  goto :fail
)

echo. & echo [8/8] Done.
echo Success!
echo   Installed under: %INSTALL_ROOT%
echo   Run: "%INSTALL_ROOT%\Models\Models.exe"  path\to\yourfile.apsimx
echo   Log: %LOG%
echo.
popd>nul 2>&1
exit /b 0

:fail
echo.
echo FAILED. Open "%LOG%" and scroll to the first error near the end of each step.
popd>nul 2>&1
exit /b 1
