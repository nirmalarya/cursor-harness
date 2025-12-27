"""
Claude executor for cursor-harness v3.0.

Uses Anthropic API to execute work items.
Simple implementation - no complex orchestration.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeExecutor:
    """Execute work items using Claude API."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Install: pip install anthropic")
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Set ANTHROPIC_API_KEY environment variable")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def execute(self, prompt: str, timeout_seconds: int = 1800) -> bool:
        """Execute work using Claude."""
        
        messages = [{"role": "user", "content": prompt}]
        
        # Simple agentic loop
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
                
                # Check stop reason
                if response.stop_reason == "end_turn":
                    print(f"   ✅ Claude completed (iterations: {iteration})")
                    return True
                
                # Execute tools
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
                    
                    # Add to conversation
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                else:
                    print(f"   ⚠️  Unexpected stop reason: {response.stop_reason}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Claude error: {e}")
                return False
        
        print(f"   ⚠️  Max iterations reached")
        return False
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions."""
        return [
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to project root"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "edit_file",
                "description": "Edit a file by replacing text",
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
                "description": "Run a shell command",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to run"}
                    },
                    "required": ["command"]
                }
            }
        ]
    
    def _execute_tool(self, tool_use) -> str:
        """Execute a tool."""
        
        tool_name = tool_use.name
        tool_input = tool_use.input
        
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "write_file":
                return self._write_file(tool_input["path"], tool_input["content"])
            elif tool_name == "edit_file":
                return self._edit_file(tool_input["path"], tool_input["old_str"], tool_input["new_str"])
            elif tool_name == "run_command":
                return self._run_command(tool_input["command"])
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error: {e}"
    
    def _read_file(self, path: str) -> str:
        """Read file."""
        file_path = self.project_dir / path
        if not file_path.exists():
            return f"File not found: {path}"
        return file_path.read_text()
    
    def _write_file(self, path: str, content: str) -> str:
        """Write file."""
        file_path = self.project_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Wrote {len(content)} chars to {path}"
    
    def _edit_file(self, path: str, old_str: str, new_str: str) -> str:
        """Edit file."""
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
        """Run shell command."""
        import subprocess
        
        # Safety check
        dangerous = ["rm -rf", "sudo", "chmod", "mkfs", "dd if="]
        if any(cmd in command for cmd in dangerous):
            return f"Blocked dangerous command: {command}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                timeout=30,
                text=True
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Command failed: {e}"

