@echo off
SETLOCAL EnableDelayedExpansion

:: SafeDrive Rewards - Ultimate Startup Script
:: Optimized for Windows dev environment

:: Navigate to project root
pushd "%~dp0.."

echo ====================================================
echo    SAFEDRIVE REWARDS - SYSTEM INITIALIZATION
echo ====================================================
echo.

:: 1. Database Check/Migration
echo [STEP 1/4] Validating Database Schema...
echo ----------------------------------------------------
python migrate_db.py
if %ERRORLEVEL% NEQ 0 (
    echo [!] SCHEMA ERROR: Database migration failed.
    echo Please ensure Python is in your PATH and dependencies are installed.
    popd
    pause
    exit /b %ERRORLEVEL%
)
echo [OK] Schema is up to date.
echo.

:: 2. Start Backend
echo [STEP 2/4] Launching SafeDrive Backend...
echo ----------------------------------------------------
:: Check if port 5000 is occupied
netstat -ano | findstr :5000 | findstr LISTENING > nul
if %ERRORLEVEL% EQU 0 (
    echo [!] Backend port 5000 is already in use. Assuming it's running.
) else (
    start "SafeDrive Backend" cmd /k "cd reward_backend && python main.py"
    echo [WAIT] Waiting for server to stabilize...
    timeout /t 10 /nobreak > nul
)
echo.

:: 3. Health Check
echo [STEP 3/4] Running Connectivity Audit...
echo ----------------------------------------------------
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 } }"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Backend is ONLINE at http://127.0.0.1:5000
) else (
    echo [CRITICAL] Backend unreachable! 
    echo Please check the 'SafeDrive Backend' window for tracebacks.
    popd
    pause
    exit /b 1
)
echo.

:: 4. Start Flutter App
echo [STEP 4/4] Launching Mobile Application...
echo ----------------------------------------------------
echo [INFO] Deep-linked with Theme ^& Accessibility refinements.
echo [INFO] Targeting active Android/Emulator.
echo.
cd reward_user_app
flutter run

if %ERRORLEVEL% NEQ 0 (
    echo [!] FLUTTER ERROR: Deployment failed. 
    echo Check your connected devices with 'flutter devices'.
)

popd
echo ----------------------------------------------------
echo SafeDrive Rewards - Startup Sequence Complete.
echo ----------------------------------------------------
pause
