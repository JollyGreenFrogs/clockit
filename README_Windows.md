# ClockIt - Professional Time Tracker (Windows Distribution)

## Quick Start

1. **Double-click `start_clockit.bat`** to launch the application
2. The application will automatically open in your web browser at `http://localhost:8000`
3. To stop the application, close the command window or press `Ctrl+C`

## Alternative Start Method

You can also run `ClockIt.exe` directly from the command line or by double-clicking it.

## Features

✅ **Task Management** - Create and organize tasks with categories
✅ **Time Tracking** - Add multiple time entries to tasks
✅ **Rate Configuration** - Set day rates with automatic hourly conversion
✅ **Invoice Generation** - Generate invoices with task bundling
✅ **Export Tracking** - Prevents double-billing exported tasks
✅ **Microsoft Planner Integration** - Sync tasks from MS Planner (optional)
✅ **Professional UI** - Modern, responsive web interface

## File Structure

- `ClockIt.exe` - Main application executable
- `start_clockit.bat` - Easy startup script
- `tasks_data.json` - Your task and time tracking data
- `rates_config.json` - Your rate configurations
- `exported_tasks.json` - Tracking of exported invoices
- `planner_config.json` - MS Planner configuration (create if needed)

## Data Backup

Your data is stored in JSON files in the same directory as the application:
- Back up `tasks_data.json` to preserve your tasks and time entries
- Back up `rates_config.json` to preserve your rate configurations
- Back up `exported_tasks.json` to maintain invoice export history

## Microsoft Planner Setup (Optional)

1. Click "Setup" in the Microsoft Planner section
2. Follow the instructions to register an Azure AD app
3. Create `planner_config.json` with your credentials

## Troubleshooting

**Port Already in Use**: If you get a port conflict, make sure no other application is using port 8000.

**Browser Doesn't Open**: Manually navigate to `http://localhost:8000` in any web browser.

**Data Loss**: Always backup your JSON files before moving the application.

## System Requirements

- Windows 10/11
- No additional software required (standalone executable)

## Support

This is a self-contained application. All dependencies are included in the executable.

Built with PyInstaller for Windows compatibility.
