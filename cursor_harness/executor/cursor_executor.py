"""
Cursor executor for cursor-harness v3.0.

Uses cursor-agent CLI which:
- Uses Cursor's logged-in auth (no API key!)
- Auto-loads MCP servers from ~/.cursor/mcp.json (Puppeteer, Azure DevOps, etc)
- Streams output in real-time

References:
- https://cursor.com/docs/cli/using
- https://cursor.com/docs/cli/mcp
"""

import subprocess
import tempfile
from pathlib import Path


class CursorExecutor:
    """
    Execute sessions using cursor-agent CLI.
    
    cursor-agent uses Cursor's logged-in auth automatically - no API key needed!
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        
        # Check if cursor-agent is available
        try:
            subprocess.run(
                ["cursor-agent", "--version"],
                capture_output=True,
                timeout=5,
                check=True
            )
            print("   ✅ cursor-agent found")
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise ValueError(
                "cursor-agent not found!\n"
                "Install: curl https://cursor.com/install -fsS | bash\n"
                "Then login to Cursor IDE"
            )
    
    def execute(self, prompt: str, timeout_seconds: int = 3600) -> bool:
        """
        Execute a session using cursor-agent CLI.
        
        Args:
            prompt: Full prompt (initializer or coding)
            timeout_seconds: Max time for this session
        
        Returns:
            True if session completed successfully
        """
        
        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            print(f"   🚀 Starting cursor-agent session...")
            
            # Run cursor-agent with:
            # -p: Non-interactive print mode for scripts
            # --force: Allow file modifications without confirmation
            # --output-format stream-json: Real-time streaming
            # --stream-partial-output: Stream text character-by-character
            # 
            # MCP servers auto-loaded from ~/.cursor/mcp.json:
            # - Puppeteer (browser automation for E2E testing)
            # - Azure DevOps (work item management)
            # - Any other configured MCP servers
            
            process = subprocess.Popen(
                [
                    "cursor-agent",
                    "-p",
                    "--force",
                    "--output-format", "stream-json",
                    "--stream-partial-output",
                    prompt  # Pass prompt directly as argument
                ],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Stream output in real-time
            tool_count = 0
            accumulated_text = ""
            
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    import json
                    event = json.loads(line)
                    event_type = event.get('type', '')
                    subtype = event.get('subtype', '')
                    
                    if event_type == 'system' and subtype == 'init':
                        model = event.get('model', 'unknown')
                        print(f"   🤖 Model: {model}")
                    
                    elif event_type == 'assistant':
                        # Accumulate text
                        content = event.get('message', {}).get('content', [])
                        if content and len(content) > 0:
                            text = content[0].get('text', '')
                            accumulated_text += text
                            # Show progress
                            if len(accumulated_text) % 100 == 0:
                                print(f"\r   📝 Generating: {len(accumulated_text)} chars", end='', flush=True)
                    
                    elif event_type == 'tool_call':
                        if subtype == 'started':
                            tool_count += 1
                            tool_call = event.get('tool_call', {})
                            
                            if 'writeToolCall' in tool_call:
                                path = tool_call['writeToolCall'].get('args', {}).get('path', 'unknown')
                                print(f"\n   🔧 Tool #{tool_count}: Writing {path}")
                            elif 'readToolCall' in tool_call:
                                path = tool_call['readToolCall'].get('args', {}).get('path', 'unknown')
                                print(f"\n   📖 Tool #{tool_count}: Reading {path}")
                            elif 'editToolCall' in tool_call:
                                path = tool_call['editToolCall'].get('args', {}).get('path', 'unknown')
                                print(f"\n   ✏️  Tool #{tool_count}: Editing {path}")
                            elif 'bashToolCall' in tool_call:
                                cmd = tool_call['bashToolCall'].get('args', {}).get('command', 'unknown')
                                print(f"\n   💻 Tool #{tool_count}: Running {cmd[:50]}")
                        
                        elif subtype == 'completed':
                            tool_call = event.get('tool_call', {})
                            
                            if 'writeToolCall' in tool_call:
                                result = tool_call['writeToolCall'].get('result', {}).get('success', {})
                                lines = result.get('linesCreated', 0)
                                size = result.get('fileSize', 0)
                                print(f"      ✅ Created {lines} lines ({size} bytes)")
                            elif 'readToolCall' in tool_call:
                                result = tool_call['readToolCall'].get('result', {}).get('success', {})
                                lines = result.get('totalLines', 0)
                                print(f"      ✅ Read {lines} lines")
                    
                    elif event_type == 'result':
                        duration = event.get('duration_ms', 0)
                        print(f"\n   ⏱️  Session: {duration}ms ({tool_count} tools)")
                
                except json.JSONDecodeError:
                    # Not JSON, probably regular output
                    print(f"   {line}")
            
            # Wait for completion
            returncode = process.wait(timeout=timeout_seconds)
            
            if returncode == 0:
                print(f"\n   ✅ Session successful!")
                return True
            else:
                print(f"\n   ⚠️  Session completed with code {returncode}")
                stderr = process.stderr.read()
                if stderr:
                    print(f"   Errors: {stderr[:200]}")
                return returncode == 0
                
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"\n   ⏰ Session timeout ({timeout_seconds}s)")
            return False
        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return False
        finally:
            # Clean up
            Path(prompt_file).unlink(missing_ok=True)
