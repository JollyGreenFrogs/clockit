#!/bin/bash

# WSL to Windows Build Script for ClockIt
# This script prepares the project for Windows compilation

set -e

echo "🚀 ClockIt WSL to Windows Build Preparation"
echo "==========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in WSL
if ! grep -qi microsoft /proc/version; then
    echo -e "${RED}❌ This script is designed for WSL (Windows Subsystem for Linux)${NC}"
    exit 1
fi

echo -e "${BLUE}📍 Current directory: $(pwd)${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🔨 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}⚡ Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${BLUE}📦 Installing requirements...${NC}"
pip install -r requirements.txt

# Install PyInstaller for Windows cross-compilation
echo -e "${BLUE}📦 Installing PyInstaller...${NC}"
pip install pyinstaller==6.14.2

# Create Windows-compatible requirements file
echo -e "${BLUE}📄 Creating Windows requirements file...${NC}"
cat > requirements_windows.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
requests==2.31.0
msal==1.24.0
pydantic==2.5.0
pathlib
datetime
typing
EOF

# Test that all imports work
echo -e "${BLUE}🧪 Testing imports...${NC}"
python -c "
import fastapi
import uvicorn
import requests
import msal
import pydantic
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
print('✅ All imports successful')
"

# Create Windows-specific spec file
echo -e "${BLUE}📝 Creating Windows PyInstaller spec file...${NC}"
cat > clockit_windows.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['clockit_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('main.py', '.'),
        ('ms_planner_integration.py', '.'),
        ('requirements.txt', '.'),
        ('*.json', '.'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'click',
        'fastapi.middleware',
        'fastapi.middleware.cors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClockIt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
EOF

# Create cross-platform build instructions
echo -e "${BLUE}📋 Creating build instructions...${NC}"
cat > BUILD_FROM_WSL.md << 'EOF'
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
EOF

# Show next steps
echo ""
echo -e "${GREEN}✅ WSL Build Preparation Complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. 📖 Read BUILD_FROM_WSL.md for detailed instructions"
echo "2. 🚀 Recommended: Copy project to Windows filesystem and build there"
echo "3. 🔧 Alternative: Use GitHub Actions for automated building"
echo ""
echo -e "${BLUE}📁 Files created:${NC}"
echo "   • clockit_windows.spec (Windows PyInstaller config)"
echo "   • requirements_windows.txt (Windows dependencies)"
echo "   • BUILD_FROM_WSL.md (Detailed build instructions)"
echo ""
echo -e "${GREEN}🎯 Ready for Windows compilation!${NC}"

# Check if Windows filesystem is accessible
if [ -d "/mnt/c" ]; then
    echo ""
    echo -e "${BLUE}💡 Tip: Your Windows C: drive is accessible at /mnt/c${NC}"
    echo "   Consider copying project to /mnt/c/Users/\$USER/Desktop/ for easier Windows access"
fi
