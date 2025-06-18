#!/usr/bin/env python3
"""
Setup script for AI Studio Automated API Server
Helps configure the required URLs before running the main server.
"""

import os
import sys

def main():
    print("="*60)
    print("   AI Studio Automated API Server - Setup")
    print("="*60)
    
    script_path = "api_server.py"
    
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found in current directory")
        sys.exit(1)
    
    print("\nTo use this automated system, you need to configure two URLs:")
    print("\n1. Google Drive Folder URL:")
    print("   - Go to Google Drive and create a folder")
    print("   - Open the folder and copy the URL from your browser")
    print("   - Example: https://drive.google.com/drive/folders/1ABC2DEF3GHI4JKL5MNO6PQR7STU8VWX9YZ")
    
    print("\n2. AI Studio Project URL:")
    print("   - Go to Google AI Studio (https://aistudio.google.com/)")
    print("   - Create or open a project")
    print("   - Copy the URL from your browser")
    print("   - Example: https://aistudio.google.com/app/prompts/1ABC2DEF3GHI4JKL5MNO6PQR")
    
    print("\n" + "="*60)
    
    drive_url = input("Enter your Google Drive folder URL: ").strip()
    if not drive_url.startswith("https://drive.google.com/"):
        print("Warning: URL should start with https://drive.google.com/")
    
    aistudio_url = input("Enter your AI Studio project URL: ").strip()
    if not aistudio_url.startswith("https://aistudio.google.com/"):
        print("Warning: URL should start with https://aistudio.google.com/")
    
    # Read the current file
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the placeholder URLs
    content = content.replace(
        "DRIVE_FOLDER_URL = 'https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE'",
        f"DRIVE_FOLDER_URL = '{drive_url}'"
    )
    content = content.replace(
        "AISTUDIO_URL = 'https://aistudio.google.com/app/prompts/YOUR_PROJECT_ID_HERE'",
        f"AISTUDIO_URL = '{aistudio_url}'"
    )
    
    # Write back to file
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("Configuration complete!")
    print("You can now run: python api_server.py")
    print("="*60)

if __name__ == "__main__":
    main()
