@echo off
echo ================================================
echo ClockIt Windows EXE Builder
echo Building from C:\Scratch\clockit_windows_build
echo ================================================
echo.

REM Change to the project directory
cd /d "C:\Scratch\clockit_windows_build"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.12+ from python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv_windows" (
    echo 🔨 Creating Windows virtual environment...
    python -m venv venv_windows
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo ⚡ Activating virtual environment...
call venv_windows\Scripts\activate.bat

echo 📦 Installing/upgrading pip...
python -m pip install --upgrade pip

echo 📦 Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo 📦 Installing PyInstaller...
pip install pyinstaller==6.14.2
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo 🏗️ Building ClockIt.exe with PyInstaller...
pyinstaller clockit_windows.spec --clean
if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ BUILD SUCCESSFUL!
echo ================================================
echo.
echo 📁 Your ClockIt.exe is ready at:
echo    C:\Scratch\clockit_windows_build\dist\ClockIt.exe
echo.
echo 🚀 To test the executable:
echo    1. Navigate to the dist folder
echo    2. Double-click ClockIt.exe
echo    3. It should open your browser to http://localhost:8000
echo.
echo 📦 To create distribution package:
echo    Run: create_distribution.bat
echo.

REM Test if the exe was created
if exist "dist\ClockIt.exe" (
    echo ✅ ClockIt.exe verified - file exists!
    dir "dist\ClockIt.exe"
) else (
    echo ❌ ClockIt.exe not found in dist folder
)

echo.
echo Press any key to exit...
pause >nul
