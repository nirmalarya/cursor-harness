"""
Cursor + MCP Hybrid Client
===========================

DEPRECATED: Cursor CLI's MCP implementation is fundamentally broken in headless mode.

Use ClaudeSDKClient instead (set ANTHROPIC_API_KEY).

This file kept for reference/future Cursor CLI fixes.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from .mcp_manager import MCPManager, create_mcp_manager_from_cursor_config


class CursorMCPClient:
    """
    Hybrid client: Cursor CLI for AI + Direct MCP for tools.
    
    This solves Cursor CLI's MCP limitation while keeping the AI working.
    """
    
    def __init__(
        self,
        project_dir: Path,
        model: str = "sonnet-4.5",
        mcp_manager: Optional[MCPManager] = None
    ):
        self.project_dir = project_dir
        self.model = model
        self.mcp_manager = mcp_manager or create_mcp_manager_from_cursor_config()
    
    async def run_session(self, prompt: str) -> Tuple[str, str]:
        """
        Run a single agent session.
        
        Uses Cursor CLI for AI reasoning + Direct MCP for tools.
        
        Args:
            prompt: The prompt to send to the agent
        
        Returns:
            (status, response) where status is "continue" or "error"
        """
        
        print(f"Running Cursor agent session (with MCP support)...")
        print(f"  Model: {self.model}")
        print(f"  Project: {self.project_dir}")
        print(f"  MCP Servers: {len(self.mcp_manager.servers)}")
        print()
        
        # Augment prompt with MCP availability info
        mcp_tools_available = self._get_mcp_tools_list()
        augmented_prompt = f"""
{prompt}

---

## 🔧 MCP Tools Available

The following MCP tools are available for you to use:

{mcp_tools_available}

**Important:** These tools are managed by the harness. You can reference them in your implementation plans, and the harness will execute them.

---
"""
        
        # Use cursor-agent (standalone command, not subcommand!)
        # Per official docs: https://cursor.com/docs/cli/mcp
        cmd = [
            "cursor-agent",
            "-p",  # Print mode
            "--force",  # Allow file modifications
            "--approve-mcps",  # Auto-approve MCP servers
            augmented_prompt,
        ]
        
        try:
            # Run cursor agent
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                timeout=3600,  # 1 hour timeout per session
            )
            
            if result.returncode == 0:
                print("\n✅ Session complete")
                return "continue", ""
            else:
                print(f"\n❌ Session failed (exit code: {result.returncode})")
                return "error", ""
        
        except subprocess.TimeoutExpired:
            print("❌ Session timed out (1 hour limit)")
            return "error", "Session timeout"
        
        except FileNotFoundError:
            print("❌ Cursor CLI not found!")
            return "error", "Cursor CLI not found"
        
        except Exception as e:
            print(f"❌ Error running session: {e}")
            return "error", str(e)
    
    def _get_mcp_tools_list(self) -> str:
        """Get formatted list of available MCP tools."""
        tools_desc = []
        
        if "azure-devops" in self.mcp_manager.servers:
            tools_desc.append("""
**Azure DevOps MCP:**
- Query work items (search, filter by epic/state)
- Get work item details
- Add comments to work items
- Update work item fields
- Mark work items as Done
""")
        
        if "playwright" in self.mcp_manager.servers:
            tools_desc.append("""
**Playwright MCP:**
- Navigate to URLs
- Click elements
- Fill forms
- Take screenshots
- Verify page content
""")
        
        if "puppeteer" in self.mcp_manager.servers:
            tools_desc.append("""
**Puppeteer MCP:**
- Navigate to URLs
- Click elements
- Fill forms
- Take screenshots
- Execute JavaScript
""")
        
        return "\n".join(tools_desc) if tools_desc else "None configured"
    
    def __enter__(self):
        """Start MCP servers when entering context."""
        self.mcp_manager.start_all()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop MCP servers when exiting context."""
        self.mcp_manager.stop_all()


def check_cursor_prerequisites() -> Tuple[bool, str]:
    """
    Check if cursor-agent CLI is installed.
    
    Returns:
        (is_ready, error_message)
    """
    try:
        result = subprocess.run(
            ["cursor-agent", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, ""
        else:
            return False, "cursor-agent not working"
    except FileNotFoundError:
        return False, """
cursor-agent not found!

Please install Cursor CLI:
  curl https://cursor.com/install -fsS | bash

Then ensure cursor-agent is available:
  cursor-agent --version
"""
    except Exception as e:
        return False, f"Error checking cursor-agent: {e}"

