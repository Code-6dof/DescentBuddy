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
