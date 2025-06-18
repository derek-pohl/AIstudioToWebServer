#!/usr/bin/env python3
"""
Simple test to check if the automation can be initialized
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_server import AIStudioAutomation, BROWSER_DATA_DIR

async def test_browser_init():
    """Test browser initialization"""
    print("Testing browser initialization...")
    
    automation = AIStudioAutomation()
    
    try:
        await automation.initialize_browser(headless=True)  # Use headless for testing
        print("✓ Browser initialized successfully")
        
        print(f"✓ Browser data dir: {BROWSER_DATA_DIR}")
        print(f"✓ Authentication status: {automation.is_authenticated}")
        
        return True
        
    except Exception as e:
        print(f"❌ Browser initialization failed: {e}")
        return False
        
    finally:
        try:
            await automation.close()
            print("✓ Browser closed successfully")
        except Exception as e:
            print(f"⚠ Warning: Could not close browser: {e}")

def main():
    print("="*50)
    print("  Browser Automation Test")
    print("="*50)
    
    try:
        result = asyncio.run(test_browser_init())
        
        if result:
            print("\n✓ Browser automation is working!")
            print("\nYou can now run the API server:")
            print("python api_server.py")
        else:
            print("\n❌ Browser automation test failed")
            print("Please check that Playwright is properly installed:")
            print("python -m playwright install")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
