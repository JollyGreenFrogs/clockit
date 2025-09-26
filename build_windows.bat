@echo off
echo ================================================================
echo           ClockIt - Windows Build Script
echo ================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12 or later from python.org
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Clean previous builds
if exist "build" (
    echo 🧹 Cleaning previous build...
    rmdir /s /q build
)

if exist "dist" (
    echo 🧹 Cleaning previous dist...
    rmdir /s /q dist
)

REM Build the executable
echo 🔨 Building ClockIt.exe...
pyinstaller clockit.spec --clean

REM Check if build was successful
if exist "dist\ClockIt.exe" (
    echo.
    echo ================================================================
    echo ✅ SUCCESS! ClockIt.exe has been created!
    echo ================================================================
    echo.
    echo 📁 Location: %cd%\dist\ClockIt.exe
    echo 📦 Size: 
    dir "dist\ClockIt.exe" | find "ClockIt.exe"
    echo.
    echo 🚀 You can now distribute the 'dist' folder to users
    echo 💡 Users can run ClockIt.exe directly - no installation needed!
    echo.
    echo Press any key to test the application...
    pause >nul
    cd dist
    ClockIt.exe
) else (
    echo.
    echo ❌ ERROR: Build failed! ClockIt.exe was not created.
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)
