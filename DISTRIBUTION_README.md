# ClockIt - Professional Time Tracker

## 🚀 Quick Start

ClockIt is a professional time tracking application that runs locally on your computer. No internet connection required after initial setup!

### 📁 What's Included

- `ClockIt` - The main executable (Linux version)
- `ClockIt.exe` - Windows executable (when compiled on Windows)
- `start_clockit.bat` - Windows batch file for easy startup
- All configuration files and data storage

### 🖥️ System Requirements

**Windows:**
- Windows 10 or Windows 11
- No additional software required

**Linux:**
- Any modern Linux distribution
- No additional software required

### 🎯 Running ClockIt

#### Windows Users:
1. Double-click `ClockIt.exe` or run `start_clockit.bat`
2. The application will automatically open in your default browser
3. Access the interface at `http://localhost:8000` (or the next available port)

#### Linux Users:
1. Make executable: `chmod +x ClockIt`
2. Run: `./ClockIt`
3. The application will automatically open in your default browser

### ✨ Features

- **Task Management**: Create, edit, and organize tasks
- **Time Tracking**: Start/stop timers with precise time logging
- **Editable Rates**: Configure hourly rates for different types of work
- **Invoice Generation**: Generate professional invoices with time summaries
- **Data Persistence**: All data is stored locally in JSON files
- **Professional UI**: Modern, responsive design that works on all devices
- **MS Planner Integration**: Connect with Microsoft Planner (optional)

### 📂 Data Storage

All your data is stored locally in:
- `tasks_data.json` - Your tasks and time entries
- `rates_config.json` - Hourly rates configuration
- Configuration files are automatically created on first run

### 🔧 Configuration

#### Setting Up Rates:
1. Navigate to the "Rates" section in the web interface
2. Click "Add New Rate" to create rate categories
3. Edit or delete rates as needed

#### MS Planner Integration (Optional):
1. Edit `planner_config_sample.json` with your Microsoft credentials
2. Rename to `planner_config.json`
3. Follow the setup instructions in `PLANNER_SETUP.md`

### 🚨 Troubleshooting

**Port Already in Use:**
- ClockIt automatically finds the next available port (8000-8009)
- Check the console output for the actual port being used

**Browser Doesn't Open:**
- Manually navigate to `http://localhost:8000` (or the displayed port)
- Ensure no firewall is blocking the application

**Data Not Saving:**
- Ensure the application has write permissions in its directory
- Check that JSON files aren't read-only

### 🔒 Privacy & Security

- **100% Local**: All data stays on your computer
- **No Internet Required**: Works completely offline
- **No Data Collection**: ClockIt doesn't send any data anywhere
- **Open Source**: Built with FastAPI, HTML, CSS, and JavaScript

### 📊 Using the Interface

1. **Dashboard**: Overview of recent tasks and quick actions
2. **Tasks**: Create and manage your tasks
3. **Time Tracking**: Start/stop timers and view time logs
4. **Rates**: Configure hourly rates for different work types
5. **Invoices**: Generate professional invoices based on tracked time

### 🆘 Support

For issues or questions:
1. Check this README for common solutions
2. Verify all files are in the same directory
3. Ensure you have proper permissions to run the executable

### 📜 License

ClockIt is open source software. Feel free to modify and distribute according to your needs.

---

**Version**: 1.0
**Build Date**: $(date)
**Compatible with**: Windows 10/11, Linux

🎉 **Thank you for using ClockIt!** 🎉
