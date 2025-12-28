"""
Cursor executor for cursor-harness v3.0.

Based on Anthropic's autonomous-coding demo pattern.
Enhanced for multiple modes and production use.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False




# ============================================================================
# Cursor Executor - Uses Cursor's auth (like Anthropic's demo uses API key)
# ============================================================================

class CursorExecutor:
    """
    Execute work items using Cursor's authentication.
    
    Pattern based on Anthropic's autonomous-coding demo.
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Install: pip install anthropic")
        
        # Use Cursor's auth (no API key needed!)
        self.client = self._get_cursor_client()
        self.model = "claude-sonnet-4-20250514"
    
    def _get_cursor_client(self) -> Anthropic:
        """Get Anthropic client using Cursor's auth or API key."""
        
        # Try Cursor's stored token
        cursor_token = self._get_cursor_token()
        if cursor_token:
            print("   ✅ Using Cursor subscription")
            return Anthropic(api_key=cursor_token)
        
        # Fallback to API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            print("   ✅ Using ANTHROPIC_API_KEY")
            return Anthropic(api_key=api_key)
        
        raise ValueError(
            "No authentication found!\n"
            "Either login to Cursor or set ANTHROPIC_API_KEY"
        )
    
    def _get_cursor_token(self) -> Optional[str]:
        """Get Cursor's stored auth token."""
        
        possible_paths = [
            Path.home() / "Library/Application Support/Cursor/User/globalStorage/storage.json",
            Path.home() / ".config/Cursor/User/globalStorage/storage.json",
            Path(os.getenv("APPDATA", "")) / "Cursor/User/globalStorage/storage.json",
        ]
        
        for config_path in possible_paths:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                    token = config.get("anthropic.apiKey") or config.get("apiKey")
                    if token:
                        return token
                except:
                    pass
        
        return None
    
    def execute(self, prompt: str) -> bool:
        """
        Execute a session using Claude.
        
        Args:
            prompt: Full prompt (initializer or coding)
        
        Returns:
            True if session completed successfully
        """
        
        # Use prompt directly (it's already complete from prompts/*.md)
        messages = [{"role": "user", "content": prompt}]
        
        iteration = 0
        max_iterations = 50
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=8000,
                    messages=messages,
                    tools=self._get_tools()
                )
                
                # Check if agent is done
                if response.stop_reason == "end_turn":
                    print(f"   ✅ Completed ({iteration} iterations)")
                    return True
                
                # Execute tool calls
                if response.stop_reason == "tool_use":
                    tool_results = []
                    
                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._execute_tool(block)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })
                    
                    # Continue conversation
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                else:
                    print(f"   ⚠️  Unexpected stop: {response.stop_reason}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return False
        
        print(f"   ⚠️  Max iterations reached")
        return False
    
    def _get_tools(self):
        """Tool definitions (like Anthropic's demo)."""
        return [
            {
                "name": "read_file",
                "description": "Read file contents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "edit_file",
                "description": "Edit file by replacing text",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_str": {"type": "string"},
                        "new_str": {"type": "string"}
                    },
                    "required": ["path", "old_str", "new_str"]
                }
            },
            {
                "name": "run_command",
                "description": "Run shell command",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            }
        ]
    
    def _execute_tool(self, tool_use) -> str:
        """Execute a tool call (like Anthropic's demo)."""
        
        try:
            if tool_use.name == "read_file":
                return self._read_file(tool_use.input["path"])
            elif tool_use.name == "write_file":
                return self._write_file(tool_use.input["path"], tool_use.input["content"])
            elif tool_use.name == "edit_file":
                return self._edit_file(tool_use.input["path"], tool_use.input["old_str"], tool_use.input["new_str"])
            elif tool_use.name == "run_command":
                return self._run_command(tool_use.input["command"])
            else:
                return f"Unknown tool: {tool_use.name}"
        except Exception as e:
            return f"Error: {e}"
    
    def _read_file(self, path: str) -> str:
        file_path = self.project_dir / path
        if not file_path.exists():
            return f"File not found: {path}"
        return file_path.read_text()
    
    def _write_file(self, path: str, content: str) -> str:
        file_path = self.project_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Wrote {len(content)} chars to {path}"
    
    def _edit_file(self, path: str, old_str: str, new_str: str) -> str:
        file_path = self.project_dir / path
        if not file_path.exists():
            return f"File not found: {path}"
        
        content = file_path.read_text()
        if old_str not in content:
            return f"String not found in {path}"
        
        new_content = content.replace(old_str, new_str, 1)
        file_path.write_text(new_content)
        return f"Edited {path}"
    
    def _run_command(self, command: str) -> str:
        """Run command with safety checks."""
        
        # Block dangerous commands
        dangerous = ["rm -rf /", "sudo rm", "mkfs", "dd if=/dev"]
        if any(cmd in command for cmd in dangerous):
            return f"Blocked dangerous command"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                timeout=30,
                text=True
            )
            output = result.stdout + result.stderr
            return output[:1000]  # Limit output
        except Exception as e:
            return f"Command failed: {e}"
