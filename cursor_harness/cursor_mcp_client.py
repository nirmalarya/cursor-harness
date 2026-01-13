"""
Cursor + MCP Hybrid Client
===========================

DEPRECATED: Cursor CLI's MCP implementation is fundamentally broken in headless mode.

Use ClaudeSDKClient instead (set ANTHROPIC_API_KEY).

This file kept for reference/future Cursor CLI fixes.
"""

import json
import os
import subprocess
import signal
import atexit
import weakref
from pathlib import Path
from typing import Optional, Tuple

from .mcp_manager import MCPManager, create_mcp_manager_from_cursor_config

# Global registry of active cursor-agent processes
_active_processes: weakref.WeakSet = weakref.WeakSet()


def _cleanup_all_processes():
    """Called on program exit - cleanup all tracked processes."""
    for proc in list(_active_processes):
        if proc.poll() is None:  # Still running
            try:
                proc.terminate()  # Graceful shutdown first
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()  # Force kill only if needed
            except Exception:
                pass


# Register cleanup on program exit
atexit.register(_cleanup_all_processes)


class CursorMCPClient:
    """
    Hybrid client: Cursor CLI for AI + Direct MCP for tools.
    
    This solves Cursor CLI's MCP limitation while keeping the AI working.
    """
    
    def __init__(
        self,
        project_dir: Path,
        model: str = "sonnet-4.5",
        mcp_manager: Optional[MCPManager] = None,
        loop_detector: Optional[Any] = None
    ):
        self.project_dir = project_dir
        self.model = model
        # Don't spawn MCPs ourselves! cursor-agent handles them automatically
        self.mcp_manager = None
        self.loop_detector = loop_detector
        self.process = None  # Will hold cursor-agent process

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        print(f"\n[Cursor Agent] Received signal {signum}, shutting down...")
        self._cleanup_process()
        import sys
        sys.exit(0)
    
    async def run_session(self, prompt: str) -> Tuple[str, str]:
        """
        Run a single agent session.
        
        Uses Cursor CLI for AI reasoning + Direct MCP for tools.
        
        Args:
            prompt: The prompt to send to the agent
        
        Returns:
            (status, response) where status is "continue" or "error"
        """
        
        print(f"Running cursor-agent session...")
        print(f"  Model: {self.model}")
        print(f"  Project: {self.project_dir}")
        print(f"  MCPs: Auto-loaded from ~/.cursor/mcp.json")
        print()
        
        # cursor-agent auto-discovers MCPs, no need to augment prompt
        augmented_prompt = prompt
        
        # Use cursor-agent with streaming for real-time progress
        # Per official docs: https://cursor.com/docs/cli/headless
        cmd = [
            "cursor-agent",
            "-p",  # Print mode
            "--force",  # Allow file modifications
            "--approve-mcps",  # Auto-approve MCP servers
            "--output-format", "stream-json",  # Stream events in real-time
            "--stream-partial-output",  # Stream partial text deltas
            augmented_prompt,
        ]
        
        try:
            # Run cursor agent with real-time streaming
            process = subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Track process for cleanup
            self.process = process
            _active_processes.add(process)
            
            # Parse and display streaming JSON events
            tool_count = 0
            accumulated_text = ""
            last_text = ""  # Track to avoid duplicates
            
            for line in process.stdout:
                try:
                    event = json.loads(line.strip())
                    event_type = event.get('type', '')
                    subtype = event.get('subtype', '')
                    
                    if event_type == 'assistant':
                        # Accumulate text deltas
                        if 'message' in event and 'content' in event['message']:
                            for content_block in event['message']['content']:
                                if 'text' in content_block:
                                    text = content_block['text']
                                    # Avoid printing duplicates
                                    if text != last_text:
                                        accumulated_text += text
                                        print(text, end='', flush=True)
                                        last_text = text
                    
                    elif event_type == 'tool_call':
                        if subtype == 'started':
                            tool_count += 1
                            tool_call = event.get('tool_call', {})
                            
                            # Compact tool output
                            if 'writeToolCall' in tool_call:
                                path = tool_call['writeToolCall'].get('args', {}).get('path', 'unknown')
                                # Shorten path for readability
                                if len(path) > 60:
                                    path = "..." + path[-57:]
                                print(f"\n✏️  #{tool_count}: Write {path}", flush=True)
                            elif 'readToolCall' in tool_call:
                                path = tool_call['readToolCall'].get('args', {}).get('path', 'unknown')
                                if len(path) > 60:
                                    path = "..." + path[-57:]
                                print(f"\n📖 #{tool_count}: Read {path}", flush=True)
                            elif 'bashToolCall' in tool_call:
                                cmd_str = tool_call['bashToolCall'].get('args', {}).get('command', 'unknown')
                                if len(cmd_str) > 50:
                                    cmd_str = cmd_str[:47] + "..."
                                print(f"\n⚡ #{tool_count}: {cmd_str}", flush=True)
                        
                        elif subtype == 'completed':
                            # Don't print "Done" for every tool (too verbose)
                            # Just show completion inline with next tool
                            pass
                    
                    elif event_type == 'result':
                        duration = event.get('duration_ms', 0)
                        duration_sec = duration / 1000
                        print(f"\n\n✅ Completed in {duration_sec:.1f}s ({tool_count} tools)\n", flush=True)
                
                except json.JSONDecodeError:
                    # Non-JSON line (error messages, etc.)
                    print(line, end='', flush=True)
            
            # Wait for completion
            returncode = process.wait(timeout=3600)
            result = type('obj', (object,), {'returncode': returncode})()

            if result.returncode == 0:
                print("\n✅ Session complete")
                self._cleanup_process()
                return "continue", ""
            else:
                print(f"\n❌ Session failed (exit code: {result.returncode})")
                self._cleanup_process()
                return "error", ""

        except subprocess.TimeoutExpired:
            print("❌ Session timed out (1 hour limit)")
            self._cleanup_process()
            return "error", "Session timeout"

        except FileNotFoundError:
            print("❌ Cursor CLI not found!")
            return "error", "Cursor CLI not found"

        except Exception as e:
            print(f"❌ Error running session: {e}")
            self._cleanup_process()
            return "error", str(e)

        finally:
            # Ensure cleanup happens even on unexpected errors
            self._cleanup_process()

    def _cleanup_process(self):
        """Clean up cursor-agent process."""
        if self.process and self.process.poll() is None:
            try:
                # Try graceful shutdown first
                self.process.terminate()
                self.process.wait(timeout=5)
                print("[Cursor Agent] Process terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill only if graceful fails
                self.process.kill()
                self.process.wait()
                print("[Cursor Agent] Process force-killed after timeout")
            except Exception as e:
                print(f"[Cursor Agent] Cleanup error: {e}")

        self.process = None

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
        """Stop MCP servers and cleanup cursor-agent process when exiting context."""
        self._cleanup_process()
        if self.mcp_manager:
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

