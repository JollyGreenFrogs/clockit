#!/usr/bin/env python3
"""
Enhanced build script for ClockIt with Desktop App support
"""

import os
import sys
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Import version info
sys.path.insert(0, 'src')
from version import get_version, get_full_version_info

def create_backend_build():
    """Create the backend executable"""
    print("🔨 Building Backend Executable")
    print("=" * 40)
    
    version_info = get_full_version_info()
    version = version_info["version"]
    
    # Clean previous builds
    print("🧹 Cleaning previous backend builds...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Run PyInstaller
    print("⚙️ Running PyInstaller...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--clean", "clockit.spec"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Backend build completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend build failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def setup_electron_backend():
    """Copy backend to electron directory"""
    print("\n🔄 Setting up Electron backend")
    print("=" * 40)
    
    # Create electron backend directory
    electron_backend_dir = Path("electron/backend")
    electron_backend_dir.mkdir(exist_ok=True)
    
    # Copy the backend executable
    if os.path.exists("dist/clockit"):
        print("📦 Copying backend executable to Electron app...")
        shutil.copy2("dist/clockit", electron_backend_dir / "clockit")
        
        # Make sure it's executable
        os.chmod(electron_backend_dir / "clockit", 0o755)
        
        print("✅ Backend copied to Electron directory")
        return True
    else:
        print("❌ Backend executable not found")
        return False

def build_electron_app():
    """Build the Electron desktop application"""
    print("\n🖥️ Building Electron Desktop App")
    print("=" * 40)
    
    # Check if Node.js is available
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js not found. Please install Node.js to build the desktop app.")
        return False
    
    # Change to electron directory
    original_dir = os.getcwd()
    try:
        os.chdir("electron")
        
        # Check if dependencies are installed
        if not os.path.exists("node_modules"):
            print("📦 Installing npm dependencies...")
            result = subprocess.run(["npm", "install"], check=True, capture_output=True, text=True)
            print("✅ Dependencies installed")
        
        # Build the Electron app
        print("🔨 Building Electron application...")
        result = subprocess.run(["npm", "run", "build-linux"], check=True, capture_output=True, text=True)
        
        print("✅ Electron desktop app built successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Electron build failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False
    finally:
        os.chdir(original_dir)

def create_releases():
    """Create versioned releases for both backend and desktop app"""
    print("\n📦 Creating Versioned Releases")
    print("=" * 40)
    
    version_info = get_full_version_info()
    version = version_info["version"]
    
    # Create release directories
    releases_dir = Path("releases")
    version_dir = releases_dir / f"v{version}"
    latest_dir = releases_dir / "latest"
    
    # Remove existing directories
    if version_dir.exists():
        shutil.rmtree(version_dir)
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Create backend release
    backend_dir = version_dir / "backend"
    backend_dir.mkdir(exist_ok=True)
    
    if os.path.exists("dist/clockit"):
        shutil.copy2("dist/clockit", backend_dir / "clockit")
        print(f"✅ Backend release created: {backend_dir}")
    
    # Create desktop app release
    desktop_dir = version_dir / "desktop"
    desktop_dir.mkdir(exist_ok=True)
    
    # Copy Electron build outputs
    electron_dist = Path("electron/dist")
    if electron_dist.exists():
        for item in electron_dist.iterdir():
            if item.is_file():
                shutil.copy2(item, desktop_dir)
            elif item.is_dir():
                shutil.copytree(item, desktop_dir / item.name, dirs_exist_ok=True)
        print(f"✅ Desktop app release created: {desktop_dir}")
    
    # Create version files
    version_file = version_dir / "version.txt"
    with open(version_file, 'w') as f:
        f.write(f"ClockIt Version: {version}\n")
        f.write(f"Build Date: {version_info['build_date']}\n")
        f.write(f"Author: {version_info['author']}\n")
        f.write(f"Description: {version_info['description']}\n")
        f.write(f"Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\nComponents:\n")
        f.write(f"- Backend Executable: backend/clockit\n")
        f.write(f"- Desktop Application: desktop/\n")
    
    # Create README
    readme_file = version_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(f"# ClockIt v{version}\n\n")
        f.write("## Professional Time Tracking & Invoice Generation\n\n")
        f.write("### 🚀 Quick Start\n\n")
        f.write("**Option 1: Desktop Application (Recommended)**\n")
        f.write("1. Extract the desktop application from `desktop/`\n")
        f.write("2. Run the ClockIt executable\n")
        f.write("3. Enjoy the native desktop experience!\n\n")
        f.write("**Option 2: Backend Only**\n")
        f.write("1. Run: `./backend/clockit`\n")
        f.write("2. Open browser to the displayed URL\n\n")
        f.write("### ✨ Features\n")
        f.write("- ⏱️ Real-time stopwatch with break adjustments\n")
        f.write("- 📋 Task management with smart categories\n")
        f.write("- 💰 Multi-currency support (100+ currencies)\n")
        f.write("- 📄 Invoice generation with export tracking\n")
        f.write("- 🔗 Microsoft Planner integration\n")
        f.write("- 🖥️ Native desktop application\n")
        f.write("- 💾 Persistent data storage\n\n")
        f.write(f"Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Copy to latest
    shutil.copytree(version_dir, latest_dir, dirs_exist_ok=True)
    
    print(f"📦 Version {version} available at: {version_dir}")
    print(f"🔗 Latest version available at: {latest_dir}")
    
    return True

def main():
    """Main build process"""
    print("🚀 ClockIt Enhanced Build Process")
    print("=" * 50)
    
    version_info = get_full_version_info()
    print(f"📦 Building ClockIt v{version_info['version']}")
    print(f"📅 Build Date: {version_info['build_date']}")
    print()
    
    success = True
    
    # Step 1: Build backend
    if not create_backend_build():
        success = False
    
    # Step 2: Setup Electron backend
    if success and not setup_electron_backend():
        success = False
    
    # Step 3: Build Electron app (optional - skip if Node.js not available)
    electron_success = build_electron_app()
    if not electron_success:
        print("⚠️ Desktop app build skipped (Node.js required)")
    
    # Step 4: Create releases
    if success:
        create_releases()
    
    if success:
        print("\n🎉 Build process completed successfully!")
        if electron_success:
            print("✅ Both backend and desktop app are ready")
            print("📁 Desktop app: releases/latest/desktop/")
        else:
            print("✅ Backend is ready")
        print("📁 Backend executable: releases/latest/backend/clockit")
        return True
    else:
        print("\n💥 Build process failed!")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
