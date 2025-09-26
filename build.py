#!/usr/bin/env python3
"""
Build script for ClockIt with versioning support
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Import version info
sys.path.insert(0, 'src')
from version import get_version, get_full_version_info

def create_versioned_build():
    """Create a versioned build of ClockIt"""
    
    print("🔨 Starting ClockIt Build Process")
    print("=" * 50)
    
    version_info = get_full_version_info()
    version = version_info["version"]
    
    print(f"📦 Building ClockIt v{version}")
    print(f"📅 Build Date: {version_info['build_date']}")
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
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
        
        print("✅ PyInstaller completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    
    # Create versioned directory structure
    releases_dir = Path("releases")
    releases_dir.mkdir(exist_ok=True)
    
    version_dir = releases_dir / f"v{version}"
    latest_dir = releases_dir / "latest"
    
    # Remove existing version and latest directories
    if version_dir.exists():
        shutil.rmtree(version_dir)
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    
    # Create version directory
    version_dir.mkdir(exist_ok=True)
    
    # Copy executable to versioned directory
    if os.path.exists("dist/clockit"):
        print(f"📁 Creating versioned release: {version_dir}")
        shutil.copy2("dist/clockit", version_dir / "clockit")
        
        # Create latest symlink/copy
        print("📁 Updating latest release...")
        shutil.copytree(version_dir, latest_dir)
        
        # Create version info file
        version_file = version_dir / "version.txt"
        with open(version_file, 'w') as f:
            f.write(f"ClockIt Version: {version}\n")
            f.write(f"Build Date: {version_info['build_date']}\n")
            f.write(f"Author: {version_info['author']}\n")
            f.write(f"Description: {version_info['description']}\n")
            f.write(f"Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Copy to latest as well
        shutil.copy2(version_file, latest_dir / "version.txt")
        
        # Create README for release
        readme_file = version_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(f"# ClockIt v{version}\n\n")
            f.write("## Professional Time Tracking & Invoice Generation\n\n")
            f.write("### Features:\n")
            f.write("- ⏱️ Real-time stopwatch with break adjustments\n")
            f.write("- 📋 Task management with categories\n")
            f.write("- 💰 Multi-currency support (100+ currencies)\n")
            f.write("- 📄 Invoice generation with export tracking\n")
            f.write("- 🔗 Microsoft Planner integration\n")
            f.write("- 💾 Persistent data storage\n\n")
            f.write("### Installation:\n")
            f.write("1. Download the `clockit` executable\n")
            f.write("2. Make it executable: `chmod +x clockit`\n")
            f.write("3. Run: `./clockit`\n")
            f.write("4. Open your browser to the displayed URL\n\n")
            f.write(f"Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        shutil.copy2(readme_file, latest_dir / "README.md")
        
        print("✅ Build completed successfully!")
        print(f"📦 Version {version} available at: {version_dir}")
        print(f"🔗 Latest version available at: {latest_dir}")
        
        return True
    else:
        print("❌ Executable not found in dist directory")
        return False

if __name__ == "__main__":
    if create_versioned_build():
        print("\n🎉 Build process completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Build process failed!")
        sys.exit(1)
