# ClockIt Windows Setup Guide

## Step 1: Install Python on Windows 11

1. Go to https://www.python.org/downloads/
2. Download Python 3.12+ (latest version)
3. Run the installer
4. ⚠️ **CRITICAL:** Check "Add Python to PATH" during installation
5. Select "Install for all users" (recommended)
6. Click "Install Now"

## Step 2: Verify Python Installation

Open Command Prompt (cmd) or PowerShell and run:
```
python --version
```
You should see something like "Python 3.12.x"

If you get "python is not recognized", Python wasn't added to PATH correctly.

## Step 3: Build ClockIt

1. Open Command Prompt as Administrator (recommended)
2. Navigate to your project:
   ```
   cd C:\Scratch\clockit_windows_build
   ```
3. Run the automated build script:
   ```
   BUILD_WINDOWS_EXE.bat
   ```

## Alternative: Manual Build Process

If you prefer manual steps:

```cmd
cd C:\Scratch\clockit_windows_build
python -m venv venv_windows
venv_windows\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller clockit_windows.spec --clean
```

## Expected Result

After successful build:
- Executable will be at: `C:\Scratch\clockit_windows_build\dist\ClockIt.exe`
- Double-click `ClockIt.exe` to run
- It should open your browser to http://localhost:8000

## Troubleshooting

**Problem:** "python is not recognized"
**Solution:** Reinstall Python and check "Add Python to PATH"

**Problem:** Build fails with dependency errors
**Solution:** Make sure you're in the correct directory and have internet connection

**Problem:** Executable doesn't run
**Solution:** Check Windows Defender/antivirus isn't blocking it

## No Python Alternative

If you don't want to install Python, you can:
1. Use GitHub Actions (automated cloud build)
2. Ask someone with Python to build it for you
3. Use online Python environments (repl.it, Google Colab)

But installing Python locally is the easiest and fastest method!
