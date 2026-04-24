@echo off
REM build_windows.bat — Build DescentBuddy as a portable Windows folder
REM Run this from the project root on a Windows machine with Python 3.10+ installed.
REM The output folder dist\DescentBuddy\ can be zipped and shared as-is.

setlocal

echo ==========================================
echo   DescentBuddy - Windows Builder
echo ==========================================

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Install dependencies
echo [1/3] Installing dependencies...
python -m pip install --quiet pyinstaller PyQt6 PyQt6-WebEngine requests
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

REM Ensure api_keys.py exists (it is gitignored; copy template if absent)
if not exist "core\api_keys.py" (
    echo [!] core\api_keys.py not found. Copying template...
    copy "core\api_keys.py.template" "core\api_keys.py" >nul
    if errorlevel 1 (
        echo ERROR: Could not copy api_keys.py.template to api_keys.py.
        pause
        exit /b 1
    )
    echo     core\api_keys.py created from template. Fill in real keys for production builds.
)

REM Fail fast if keys are still blank (template was not filled in)
findstr /C:"RDLADDER_KEY = \"\"" "core\api_keys.py" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ERROR: core\api_keys.py still contains empty Firebase keys.
    echo        Open core\api_keys.py and fill in RDLADDER_KEY and DESCENT_BUDDY_KEY
    echo        before building. These values come from your Firebase console.
    echo.
    pause
    exit /b 1
)

REM Run PyInstaller
echo [2/3] Running PyInstaller...
python -m PyInstaller descentbuddy_windows.spec --noconfirm --clean
if errorlevel 1 (
    echo ERROR: PyInstaller failed.
    pause
    exit /b 1
)

REM Verify output
if not exist "dist\DescentBuddy\DescentBuddy.exe" (
    echo ERROR: Expected dist\DescentBuddy\DescentBuddy.exe was not created.
    pause
    exit /b 1
)

echo [3/3] Done.
echo.
echo Output: dist\DescentBuddy\
echo Zip that folder and send it. The recipient runs DescentBuddy.exe inside it.
echo.
pause
