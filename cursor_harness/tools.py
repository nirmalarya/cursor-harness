"""
Tool Implementations for Anthropic API
=======================================

Implements file operations, bash execution, etc. for agent sessions.
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict


class BaseTool:
    """Base class for tools."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
    
    def execute(self, params: Dict[str, Any]) -> str:
        """Execute the tool with given parameters."""
        raise NotImplementedError


class ReadTool(BaseTool):
    """Read file contents."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        file_path = self.project_dir / params.get("target_file", "")
        
        if not file_path.exists():
            return f"Error: File not found: {file_path}"
        
        try:
            offset = params.get("offset", 0)
            limit = params.get("limit")
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            if offset or limit:
                start = offset if offset else 0
                end = start + limit if limit else len(lines)
                lines = lines[start:end]
            
            return ''.join(lines)
        except Exception as e:
            return f"Error reading file: {e}"


class WriteTool(BaseTool):
    """Write file contents."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        file_path = self.project_dir / params.get("file_path", "")
        contents = params.get("contents", "")
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(contents)
            return f"✅ Wrote {len(contents)} characters to {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"


class EditTool(BaseTool):
    """Edit file with search/replace."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        file_path = self.project_dir / params.get("file_path", "")
        old_string = params.get("old_string", "")
        new_string = params.get("new_string", "")
        
        if not file_path.exists():
            return f"Error: File not found: {file_path}"
        
        try:
            content = file_path.read_text()
            
            if old_string not in content:
                return f"Error: String not found in file"
            
            new_content = content.replace(old_string, new_string, 1)
            file_path.write_text(new_content)
            
            return f"✅ Edited {file_path}"
        except Exception as e:
            return f"Error editing file: {e}"


class BashTool(BaseTool):
    """Execute bash commands."""
    
    def __init__(self, project_dir: Path, security_validator):
        super().__init__(project_dir)
        self.security_validator = security_validator
    
    def execute(self, params: Dict[str, Any]) -> str:
        command = params.get("command", "")
        
        # Validate security
        if self.security_validator:
            is_allowed, reason = self.security_validator.validate_command(command)
            if not is_allowed:
                return f"❌ Command blocked: {reason}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_dir,
                timeout=60
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            
            return output
        except subprocess.TimeoutExpired:
            return "Error: Command timed out (60s limit)"
        except Exception as e:
            return f"Error executing command: {e}"


class GlobTool(BaseTool):
    """Find files matching pattern."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        pattern = params.get("pattern", "")
        
        try:
            matches = list(self.project_dir.glob(pattern))
            if matches:
                return '\n'.join(str(p.relative_to(self.project_dir)) for p in matches[:100])
            return "No files found"
        except Exception as e:
            return f"Error: {e}"


class GrepTool(BaseTool):
    """Search for pattern in files."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        pattern = params.get("pattern", "")
        path = params.get("path", ".")
        
        try:
            result = subprocess.run(
                ["grep", "-r", "-n", pattern, path],
                capture_output=True,
                text=True,
                cwd=self.project_dir,
                timeout=30
            )
            return result.stdout if result.stdout else "No matches found"
        except Exception as e:
            return f"Error: {e}"


class ListDirectoryTool(BaseTool):
    """List directory contents."""
    
    def execute(self, params: Dict[str, Any]) -> str:
        target = params.get("target_directory", ".")
        dir_path = self.project_dir / target
        
        if not dir_path.exists():
            return f"Error: Directory not found: {dir_path}"
        
        try:
            items = list(dir_path.iterdir())
            return '\n'.join(item.name for item in sorted(items))
        except Exception as e:
            return f"Error: {e}"

