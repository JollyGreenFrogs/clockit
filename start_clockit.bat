@echo off
title ClockIt - Professional Time Tracker
echo.
echo ================================================================
echo                   ClockIt - Time Tracker                      
echo ================================================================
echo.
echo Starting ClockIt application...
echo.
echo The application will open in your default web browser.
echo To stop the application, close this window or press Ctrl+C
echo.
echo ================================================================
echo.

:: Change to the directory where the executable is located
cd /d "%~dp0"

:: Start the application
ClockIt.exe

echo.
echo ================================================================
echo ClockIt has been stopped.
echo ================================================================
pause
