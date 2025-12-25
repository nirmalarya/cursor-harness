"""
Cursor CLI Client
=================

Executes agent sessions using Cursor's built-in AI via CLI.
No API key needed - uses your Cursor subscription!
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class CursorCLIClient:
    """Client for running agent sessions with Cursor CLI."""
    
    def __init__(
        self,
        project_dir: Path,
        model: str = "sonnet-4.5",
    ):
        self.project_dir = project_dir
        self.model = model
    
    async def run_session(self, prompt: str) -> Tuple[str, str]:
        """
        Run a single agent session using Cursor CLI.
        
        Args:
            prompt: The prompt to send to the agent
        
        Returns:
            (status, response) where status is "continue" or "error"
        """
        
        print(f"Running Cursor agent session...")
        print(f"  Model: {self.model}")
        print(f"  Project: {self.project_dir}")
        print()
        
        # Prepare cursor agent command
        cmd = [
            "cursor",
            "agent",
            "run",
            "--print",  # Print to console
            "--output-format", "text",
            prompt,
        ]
        
        try:
            # Run cursor agent
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout per session
            )
            
            if result.returncode == 0:
                print("✅ Session complete")
                return "continue", result.stdout
            else:
                print(f"❌ Session failed (exit code: {result.returncode})")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")
                return "error", result.stderr
        
        except subprocess.TimeoutExpired:
            print("❌ Session timed out (1 hour limit)")
            return "error", "Session timeout"
        
        except FileNotFoundError:
            print("❌ Cursor CLI not found!")
            print("\nIs Cursor installed?")
            print("Try: cursor --version")
            return "error", "Cursor CLI not found"
        
        except Exception as e:
            print(f"❌ Error running session: {e}")
            return "error", str(e)
    
    def check_cursor_installed(self) -> bool:
        """Check if Cursor CLI is available."""
        try:
            result = subprocess.run(
                ["cursor", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def check_cursor_logged_in(self) -> bool:
        """Check if user is logged in to Cursor."""
        try:
            result = subprocess.run(
                ["cursor", "agent", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "logged in" in result.stdout.lower()
        except:
            return False


def check_cursor_prerequisites() -> Tuple[bool, str]:
    """
    Check if Cursor CLI is installed and user is logged in.
    
    Returns:
        (is_ready, error_message)
    """
    client = CursorCLIClient(Path.cwd())
    
    if not client.check_cursor_installed():
        return False, """
Cursor CLI not found!

Please install Cursor:
  https://cursor.sh

Then ensure the CLI is available:
  cursor --version
"""
    
    if not client.check_cursor_logged_in():
        return False, """
Not logged in to Cursor!

Please log in:
  cursor agent login

Then try again.
"""
    
    return True, ""

