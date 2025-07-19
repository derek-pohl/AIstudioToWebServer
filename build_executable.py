#!/usr/bin/env python3
"""
Build script for creating standalone executables
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller"""
    
    print("Cleaning previous builds...")
    try:
        if os.path.exists('dist'):
            shutil.rmtree('dist')
    except PermissionError:
        print("Warning: Could not remove dist folder (file may be in use)")
        print("Please close any running executables and try again")
        return False
    
    try:
        if os.path.exists('build'):
            shutil.rmtree('build')
    except PermissionError:
        print("Warning: Could not remove build folder")
    
    # PyInstaller command - simple single file approach
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--name=ai-studio-server',
        '--add-data=config.json;.',
        '--hidden-import=playwright',
        '--hidden-import=playwright.async_api',
        '--collect-all=playwright',
        'api_server.py'
    ]
    
    print("Building executable with PyInstaller...")
    print("This may take 2-3 minutes, please wait...")
    
    # Run with real-time output
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                              universal_newlines=True, bufsize=1)
    
    # Show progress dots
    import time
    import threading
    
    def show_progress():
        while process.poll() is None:
            print(".", end="", flush=True)
            time.sleep(2)
    
    progress_thread = threading.Thread(target=show_progress)
    progress_thread.daemon = True
    progress_thread.start()
    
    # Wait for completion
    stdout, _ = process.communicate()
    
    if process.returncode != 0:
        print("\nBuild failed:")
        print(stdout)
        return False
    
    print("\nBuild successful!")
    
    # Create distribution folder with config
    dist_folder = Path('dist/ai-studio-server-release')
    dist_folder.mkdir(exist_ok=True)
    
    # Copy executable (single file)
    exe_name = 'ai-studio-server.exe' if sys.platform == 'win32' else 'ai-studio-server'
    shutil.copy(f'dist/{exe_name}', dist_folder)
    
    # Copy config template to the release folder
    shutil.copy('config.json', dist_folder / 'config.json')
    
    # Create README for users
    readme_content = """# AI Studio Server

## Quick Start

1. **FIRST TIME ONLY**: Install Playwright browsers
   Open Command Prompt/Terminal and run:
   ```
   python -m playwright install chromium
   ```
   (If you don't have Python, install it from python.org first)

2. Edit `config.json` and fill in your URLs:
   - Replace `drive_folder_url` with your Google Drive folder URL
   - Replace `aistudio_url` with your AI Studio prompt URL

3. Run the executable:
   - Windows: Double-click `ai-studio-server.exe`
   - Mac/Linux: `./ai-studio-server`

4. Follow the authentication prompts in your browser

## Configuration

Edit `config.json` to customize:
- Server port (default: 8383)
- Browser settings (headless mode, etc.)
- Gemini model parameters
- Timeout settings

The config file must be in the same directory as the executable.

## Troubleshooting

If you get "Playwright browsers not found":
1. Make sure Python is installed
2. Run: `python -m playwright install chromium`
3. Try running the executable again
"""
    
    with open(dist_folder / 'README.txt', 'w') as f:
        f.write(readme_content)
    
    print(f"Distribution created in: {dist_folder}")
    return True

if __name__ == '__main__':
    if build_executable():
        print("Ready for distribution!")
    else:
        print("Build failed!")
        sys.exit(1)