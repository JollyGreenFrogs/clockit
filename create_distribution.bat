@echo off
title ClockIt - Distribution Package Creator
color 0A

echo.
echo ================================================================
echo              ClockIt - Distribution Package Creator
echo ================================================================
echo.

REM Check if ClockIt.exe exists
if not exist "dist\ClockIt.exe" (
    echo ❌ ERROR: ClockIt.exe not found!
    echo Please run build_windows.bat first to create the executable.
    pause
    exit /b 1
)

echo ✅ ClockIt.exe found

REM Create distribution folder
set DIST_FOLDER=ClockIt_Windows_Distribution
if exist "%DIST_FOLDER%" (
    echo 🧹 Cleaning previous distribution...
    rmdir /s /q "%DIST_FOLDER%"
)

echo 📦 Creating distribution package...
mkdir "%DIST_FOLDER%"

REM Copy executable
echo 📋 Copying ClockIt.exe...
copy "dist\ClockIt.exe" "%DIST_FOLDER%\"

REM Copy startup script
echo 📋 Copying startup script...
copy "start_clockit.bat" "%DIST_FOLDER%\"

REM Copy documentation
echo 📋 Copying documentation...
if exist "DISTRIBUTION_README.md" copy "DISTRIBUTION_README.md" "%DIST_FOLDER%\README.md"
if exist "COMPILATION_SUCCESS.md" copy "COMPILATION_SUCCESS.md" "%DIST_FOLDER%\"

REM Create data directory
echo 📁 Creating data directory...
mkdir "%DIST_FOLDER%\clockit_data"

REM Copy sample config files if they exist
if exist "rates_config.json" copy "rates_config.json" "%DIST_FOLDER%\clockit_data\"
if exist "planner_config_sample.json" copy "planner_config_sample.json" "%DIST_FOLDER%\"

REM Create quick start guide
echo 📝 Creating Quick Start Guide...
(
echo # ClockIt - Quick Start Guide
echo.
echo ## 🚀 Getting Started
echo.
echo 1. **Run ClockIt:**
echo    - Double-click `ClockIt.exe` OR
echo    - Double-click `start_clockit.bat` for enhanced startup
echo.
echo 2. **First Use:**
echo    - ClockIt will automatically open in your web browser
echo    - If browser doesn't open, navigate to: http://localhost:8000
echo.
echo 3. **Your Data:**
echo    - All data is stored in the `clockit_data` folder
echo    - This includes tasks, rates, and generated invoices
echo.
echo 4. **Shutting Down:**
echo    - Use the "Shutdown ClockIt" button in the web interface OR
echo    - Press Ctrl+C in the console window
echo.
echo ## ✨ Features
echo.
echo - ✅ Task Management with Categories
echo - ✅ Time Tracking with Detailed Logging  
echo - ✅ Editable Hourly/Daily Rates
echo - ✅ Professional Invoice Generation
echo - ✅ Microsoft Planner Integration ^(optional^)
echo - ✅ Complete Data Export/Import
echo.
echo ## 🆘 Support
echo.
echo If you encounter any issues:
echo 1. Check that no other application is using port 8000
echo 2. Ensure you have proper permissions to run the executable
echo 3. Check the console window for error messages
echo.
echo **ClockIt automatically finds available ports 8000-8009**
echo.
echo ---
echo.
echo 🎉 **Thank you for using ClockIt!** 🎉
echo.
echo Version: 1.0 ^| Build Date: %date%
) > "%DIST_FOLDER%\QUICK_START.md"

REM Get file size
for %%A in ("dist\ClockIt.exe") do set SIZE=%%~zA

echo.
echo ================================================================
echo ✅ Distribution Package Created Successfully!
echo ================================================================
echo.
echo 📁 Package Location: %cd%\%DIST_FOLDER%
echo 📦 Executable Size: %SIZE% bytes
echo.
echo 📋 Package Contents:
echo    • ClockIt.exe          - Main application
echo    • start_clockit.bat    - Windows startup script  
echo    • README.md           - User documentation
echo    • QUICK_START.md      - Getting started guide
echo    • clockit_data\       - Data storage directory
echo.
echo 🚀 Ready for Distribution!
echo.
echo You can now:
echo 1. ZIP the '%DIST_FOLDER%' folder for easy sharing
echo 2. Copy to other Windows 10/11 computers
echo 3. No installation required - just run ClockIt.exe!
echo.
pause
