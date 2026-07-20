@echo off
setlocal EnableExtensions
REM One-command demo launcher for AgentShadow Community Edition (Windows).
cd /d "%~dp0"

if not defined AGENTSHADOW_API_URL set "AGENTSHADOW_API_URL=http://localhost:8013"
if not defined AGENTSHADOW_UI_URL set "AGENTSHADOW_UI_URL=http://localhost:3011"

if exist ".env.example" if not exist ".env" (
  echo ==^> Creating .env from .env.example...
  copy /Y ".env.example" ".env" >nul
)

echo ==^> Starting AgentShadow Community Edition (Docker)...
docker compose up --build -d
if errorlevel 1 (
  echo ERROR: docker compose failed. Is Docker Desktop running?
  exit /b 1
)

echo ==^> Waiting for API health...
set /a _tries=0
:wait_health
curl.exe -sf "%AGENTSHADOW_API_URL%/health" >nul 2>&1
if not errorlevel 1 goto healthy
set /a _tries+=1
if %_tries% geq 30 goto unhealthy
timeout /t 2 /nobreak >nul
goto wait_health

:unhealthy
echo ERROR: API did not become healthy at %AGENTSHADOW_API_URL%/health
exit /b 1

:healthy
echo ==^> Seeding demo fleet (3 risk tiers: ~35%% / ~60%% / ~89%%^)...
docker compose exec -T agentshadow-community python -m scripts.seed_demo
if errorlevel 1 (
  echo WARNING: demo seed failed — stack is up; you can seed later with:
  echo   docker compose exec -T agentshadow-community python -m scripts.seed_demo
)

echo.
echo AgentShadow Community Edition is ready.
echo.
echo   Landing page (start here)  %AGENTSHADOW_UI_URL%/
echo   Plans ^& pricing            %AGENTSHADOW_UI_URL%/pricing
echo   Executive dashboard        %AGENTSHADOW_UI_URL%/dashboard
echo   Agent inventory            %AGENTSHADOW_UI_URL%/agents
echo   Scan a repo                %AGENTSHADOW_UI_URL%/scan
echo   Governance policies        %AGENTSHADOW_UI_URL%/governance
echo.
echo   API docs                   %AGENTSHADOW_API_URL%/docs
echo   Health check               %AGENTSHADOW_API_URL%/health
echo   Edition metadata           %AGENTSHADOW_API_URL%/meta
echo.
echo Free in Community: code scan, scoring, inventory, dashboard, governance viewing.
echo Locked (upgrade):  runtime connectors, PDF reports, correlation feed.
echo.
echo Stop:  docker compose down
echo Logs:  docker compose logs -f
echo.
endlocal
exit /b 0
