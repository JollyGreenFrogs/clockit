# Building ClockIt for Windows from WSL

## Method 1: Using Windows Python from WSL

1. **Install Python for Windows** (if not already installed):
   - Download Python 3.12+ from python.org
   - Install to default location (usually C:\Python312\)

2. **Build from WSL**:
   ```bash
   # Navigate to your WSL project directory
   cd /mnt/c/path/to/your/clockit/project
   
   # Use Windows Python to create virtual environment
   /mnt/c/Python312/python.exe -m venv venv_windows
   
   # Activate Windows virtual environment
   ./venv_windows/Scripts/activate
   
   # Install requirements
   ./venv_windows/Scripts/pip.exe install -r requirements.txt
   ./venv_windows/Scripts/pip.exe install pyinstaller
   
   # Build Windows executable
   ./venv_windows/Scripts/pyinstaller.exe clockit_windows.spec
   ```

3. **Alternative: Copy project to Windows and build**:
   ```bash
   # Copy entire project to Windows filesystem
   cp -r /home/venura/scratch/clockit /mnt/c/Users/$USER/Desktop/clockit_build
   
   # Then use Windows Command Prompt or PowerShell:
   # cd C:\Users\%USERNAME%\Desktop\clockit_build
   # python -m venv venv
   # venv\Scripts\activate
   # pip install -r requirements.txt
   # pip install pyinstaller
   # pyinstaller clockit_windows.spec
   ```

## Method 2: Using Docker with Windows containers

```bash
# Build using Windows container (requires Docker Desktop with Windows containers)
docker run --rm -v $(pwd):/app -w /app python:3.12-windowsservercore-1809 cmd /c "
pip install -r requirements.txt &&
pip install pyinstaller &&
pyinstaller clockit_windows.spec
"
```

## Method 3: GitHub Actions (Recommended for CI/CD)

Create `.github/workflows/build-windows.yml`:

```yaml
name: Build Windows EXE
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - run: |
        pip install -r requirements.txt
        pip install pyinstaller
        pyinstaller clockit_windows.spec
    - uses: actions/upload-artifact@v3
      with:
        name: ClockIt-Windows
        path: dist/ClockIt.exe
```

## Files prepared for Windows build:
- ✅ clockit_windows.spec (Windows-optimized PyInstaller config)
- ✅ requirements_windows.txt (Windows-compatible dependencies)
- ✅ clockit_app.py (Windows launcher with proper signal handling)
- ✅ All necessary source files

## Quick Start:
1. Choose Method 1 above for immediate building
2. The executable will be created in `dist/ClockIt.exe`
3. Run `ClockIt.exe` on any Windows 10/11 machine (no Python required)
