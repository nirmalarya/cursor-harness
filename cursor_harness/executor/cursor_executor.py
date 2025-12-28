"""
Cursor executor for cursor-harness v3.0.

Uses cursor-agent CLI with streaming output.
Reference: https://cursor.com/docs/cli/using
"""

import subprocess
import tempfile
import json
from pathlib import Path


class CursorExecutor:
    """Execute sessions using cursor-agent CLI."""
    
    def __init__(self, project_dir: Path, loop_detector=None):
        self.project_dir = project_dir
        self.loop_detector = loop_detector
        
        # Verify cursor-agent exists
        try:
            subprocess.run(
                ["cursor-agent", "--version"],
                capture_output=True,
                timeout=5,
                check=True
            )
            print("   ✅ cursor-agent found")
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise ValueError("cursor-agent not found! Login to Cursor IDE")
    
    def execute(self, prompt: str, timeout_seconds: int = 3600) -> bool:
        """Execute a session using cursor-agent."""
        
        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            print(f"   🚀 Starting cursor-agent session...")
            
            # Start cursor-agent process
            process = subprocess.Popen(
                [
                    "cursor-agent",
                    "-p",
                    "--force",
                    "--output-format", "stream-json",
                    "--stream-partial-output",
                    "--file", prompt_file
                ],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Stream and parse output
            tool_count = 0
            accumulated_text = ""
            
            try:
                for line in process.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event = json.loads(line)
                        event_type = event.get('type', '')
                        subtype = event.get('subtype', '')
                        
                        # Handle different event types
                        if event_type == 'system' and subtype == 'init':
                            model = event.get('model', 'unknown')
                            print(f"   🤖 Model: {model}")
                        
                        elif event_type == 'assistant':
                            content = event.get('message', {}).get('content', [])
                            if content and len(content) > 0:
                                text = content[0].get('text', '')
                                accumulated_text += text
                                if len(accumulated_text) % 100 == 0:
                                    print(f"\r   📝 Generating: {len(accumulated_text)} chars", end='', flush=True)
                        
                        elif event_type == 'tool_call':
                            if subtype == 'started':
                                tool_count += 1
                                tool_call = event.get('tool_call', {})
                                
                                # Track tool for loop detection
                                if 'writeToolCall' in tool_call:
                                    path = tool_call['writeToolCall'].get('args', {}).get('path', 'unknown')
                                    print(f"\n   🔧 Tool #{tool_count}: Writing {path}")
                                    if self.loop_detector:
                                        self.loop_detector.track_tool('write', path)
                                
                                elif 'readToolCall' in tool_call:
                                    path = tool_call['readToolCall'].get('args', {}).get('path', 'unknown')
                                    print(f"\n   📖 Tool #{tool_count}: Reading {path}")
                                    if self.loop_detector:
                                        self.loop_detector.track_tool('read', path)
                                        # Check for loops
                                        is_stuck, reason = self.loop_detector.check()
                                        if is_stuck:
                                            print(f"\n   ⚠️  LOOP DETECTED: {reason}")
                                            print(f"   Stopping session...")
                                            process.kill()
                                            return False
                                
                                elif 'editToolCall' in tool_call:
                                    path = tool_call['editToolCall'].get('args', {}).get('path', 'unknown')
                                    print(f"\n   ✏️  Tool #{tool_count}: Editing {path}")
                                    if self.loop_detector:
                                        self.loop_detector.track_tool('edit', path)
                                
                                elif 'bashToolCall' in tool_call:
                                    cmd = tool_call['bashToolCall'].get('args', {}).get('command', 'unknown')
                                    print(f"\n   💻 Tool #{tool_count}: Running {cmd[:50]}")
                                    if self.loop_detector:
                                        self.loop_detector.track_tool('bash')
                            
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
                        print(f"   {line}")
                
                # Wait for process to complete
                returncode = process.wait(timeout=timeout_seconds)
                
                if returncode == 0:
                    print(f"\n   ✅ Session successful!")
                    return True
                else:
                    print(f"\n   ⚠️  Session exited with code {returncode}")
                    return False
                    
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"\n   ⏰ Session timeout ({timeout_seconds}s)")
                return False
        
        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return False
        
        finally:
            # Cleanup temp file
            Path(prompt_file).unlink(missing_ok=True)
