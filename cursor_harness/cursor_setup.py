"""
Automatic cursor-agent setup and authentication.

Ensures cursor-agent is installed and authenticated before running sessions.
"""

import subprocess
import sys
import os
from pathlib import Path


def check_cursor_agent_installed() -> bool:
    """Check if cursor-agent is installed."""
    try:
        result = subprocess.run(
            ["cursor-agent", "--version"],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_cursor_agent() -> bool:
    """
    Install cursor-agent CLI.

    Returns:
        True if installation succeeded, False otherwise
    """
    print("\n📦 cursor-agent not found. Installing...")

    # Check if npm is available
    try:
        subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            timeout=5,
            check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ npm not found. Please install Node.js first:")
        print("   https://nodejs.org/")
        return False

    # Install cursor-agent globally
    print("   Running: npm install -g @cursor/agent")
    try:
        result = subprocess.run(
            ["npm", "install", "-g", "@cursor/agent"],
            timeout=120,  # 2 minutes timeout
            text=True
        )

        if result.returncode == 0:
            print("   ✅ cursor-agent installed successfully")
            return True
        else:
            print(f"   ❌ Installation failed with exit code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Installation timed out (>2 minutes)")
        return False
    except Exception as e:
        print(f"   ❌ Installation error: {e}")
        return False


def check_cursor_agent_authenticated() -> bool:
    """
    Check if cursor-agent is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    try:
        # Try to run a command that actually requires authentication
        # Use -p with a simple prompt to test if auth works
        result = subprocess.run(
            ["cursor-agent", "-p", "echo test"],
            capture_output=True,
            timeout=10,
            text=True,
            input="test\n"  # Provide minimal input
        )

        # Check for authentication error in output
        error_output = result.stderr + result.stdout

        if "Authentication required" in error_output:
            return False

        if "login" in error_output.lower() and "required" in error_output.lower():
            return False

        if "CURSOR_API_KEY" in error_output and "required" in error_output.lower():
            return False

        # If no auth error, we're authenticated
        return True

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def authenticate_cursor_agent() -> bool:
    """
    Authenticate cursor-agent (interactive login).

    Returns:
        True if authentication succeeded, False otherwise
    """
    print("\n🔐 cursor-agent not authenticated. Starting login...")
    print("   This will open Cursor for authentication...")

    try:
        # Run cursor-agent login (interactive)
        result = subprocess.run(
            ["cursor-agent", "login"],
            timeout=300,  # 5 minutes for user to complete login
            text=True
        )

        if result.returncode == 0:
            print("   ✅ Authentication successful")
            return True
        else:
            print(f"   ❌ Authentication failed with exit code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Authentication timed out (>5 minutes)")
        return False
    except KeyboardInterrupt:
        print("\n   ⚠️  Authentication cancelled by user")
        return False
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False


def ensure_cursor_agent_ready() -> bool:
    """
    Ensure cursor-agent is installed and authenticated.

    Automatically installs and authenticates if needed.

    Returns:
        True if ready, False if setup failed
    """
    print("🔍 Checking cursor-agent setup...")

    # Step 1: Check installation
    if not check_cursor_agent_installed():
        if not install_cursor_agent():
            print("\n❌ cursor-agent installation failed")
            print("   Please install manually:")
            print("   npm install -g @cursor/agent")
            return False
    else:
        print("   ✅ cursor-agent installed")

    # Step 2: Check authentication
    if not check_cursor_agent_authenticated():
        if not authenticate_cursor_agent():
            print("\n❌ cursor-agent authentication failed")
            print("   Please authenticate manually:")
            print("   cursor-agent login")
            return False
    else:
        print("   ✅ cursor-agent authenticated")

    print("✅ cursor-agent ready!\n")
    return True


def get_cursor_agent_info() -> dict:
    """
    Get cursor-agent version and authentication status.

    Returns:
        Dict with 'version', 'installed', 'authenticated' keys
    """
    info = {
        'installed': False,
        'authenticated': False,
        'version': None
    }

    # Check installation and version
    try:
        result = subprocess.run(
            ["cursor-agent", "--version"],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            info['installed'] = True
            info['version'] = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check authentication
    if info['installed']:
        info['authenticated'] = check_cursor_agent_authenticated()

    return info
