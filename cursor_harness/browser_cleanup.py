"""
Browser Cleanup Utility
========================

Cleans up orphaned Playwright/Puppeteer browser instances.
"""

import subprocess
import time


def kill_orphaned_browsers():
    """Kill all Playwright MCP browser instances."""
    
    print("🧹 Cleaning up orphaned browser instances...")
    
    # Kill Playwright MCP browsers
    try:
        subprocess.run(
            ["pkill", "-f", "ms-playwright/mcp-chrome"],
            timeout=5
        )
        print("   ✅ Killed Playwright browsers")
    except:
        pass
    
    # Kill remote debugging browsers
    try:
        subprocess.run(
            ["pkill", "-f", "remote-debugging-port"],
            timeout=5
        )
        print("   ✅ Killed remote debugging browsers")
    except:
        pass
    
    time.sleep(1)
    
    # Check remaining
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        chrome_count = len([line for line in result.stdout.split('\n') 
                           if 'ms-playwright' in line or 'remote-debugging' in line])
        
        if chrome_count > 0:
            print(f"   ⚠️  {chrome_count} browser processes remain")
        else:
            print(f"   ✅ All browser instances cleaned up")
    except:
        pass


def setup_browser_cleanup():
    """Set up automatic browser cleanup on exit."""
    import atexit
    atexit.register(kill_orphaned_browsers)
