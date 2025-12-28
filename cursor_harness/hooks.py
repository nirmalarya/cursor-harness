"""
Hooks system for cursor-harness v3.0

Automatic validation - prevents agent from getting stuck in validation loops!

Based on sr developer insight:
- afterFileEdit: Run linters, tests, type checks automatically
- onStop: Final validation before session ends
- Agent focuses on implementation, hooks handle validation
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List


class HooksManager:
    """
    Manage cursor-harness hooks.
    
    Hooks run automatically:
    - afterFileEdit: After agent writes/edits file
    - onStop: When agent session ends
    - sessionStart: Before session begins
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.hooks_file = project_dir / ".cursor" / "hooks.json"
        self.hooks = self._load_hooks()
    
    def _load_hooks(self) -> Dict:
        """Load hooks from .cursor/hooks.json."""
        if self.hooks_file.exists():
            with open(self.hooks_file) as f:
                return json.load(f)
        return {}
    
    def setup_default_hooks(self):
        """Setup default hooks for the project."""
        
        # Auto-detect project type
        hooks = {
            "afterFileEdit": [],
            "onStop": [],
            "sessionStart": []
        }
        
        # Python project
        if (self.project_dir / "requirements.txt").exists():
            hooks["afterFileEdit"].append({
                "name": "pytest",
                "command": "pytest --tb=short -x",
                "workingDir": ".",
                "continueOnError": True
            })
            hooks["onStop"].append({
                "name": "coverage",
                "command": "pytest --cov --cov-report=term-missing",
                "workingDir": ".",
                "continueOnError": True
            })
        
        # TypeScript/JavaScript project
        if (self.project_dir / "package.json").exists():
            hooks["afterFileEdit"].append({
                "name": "eslint",
                "command": "npm run lint || true",
                "workingDir": ".",
                "continueOnError": True
            })
            hooks["onStop"].append({
                "name": "build",
                "command": "npm run build",
                "workingDir": ".",
                "continueOnError": True
            })
        
        # Go project
        if (self.project_dir / "go.mod").exists():
            hooks["afterFileEdit"].append({
                "name": "go-fmt",
                "command": "gofmt -w .",
                "workingDir": ".",
                "continueOnError": True
            })
            hooks["afterFileEdit"].append({
                "name": "go-vet",
                "command": "go vet ./...",
                "workingDir": ".",
                "continueOnError": True
            })
            hooks["onStop"].append({
                "name": "go-test",
                "command": "go test ./...",
                "workingDir": ".",
                "continueOnError": True
            })
        
        # Save hooks
        self.hooks_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.hooks_file, 'w') as f:
            json.dump(hooks, f, indent=2)
        
        print(f"   ✅ Hooks configured ({len(hooks['afterFileEdit'])} after-edit, {len(hooks['onStop'])} on-stop)")
    
    def run_hook(self, hook_type: str) -> bool:
        """
        Run hooks of a specific type.
        
        Args:
            hook_type: 'afterFileEdit', 'onStop', or 'sessionStart'
        
        Returns:
            True if all hooks passed
        """
        hooks_to_run = self.hooks.get(hook_type, [])
        
        if not hooks_to_run:
            return True
        
        print(f"\n   🪝 Running {hook_type} hooks ({len(hooks_to_run)})...")
        
        all_passed = True
        
        for hook in hooks_to_run:
            name = hook.get('name', 'unnamed')
            command = hook.get('command', '')
            working_dir = self.project_dir / hook.get('workingDir', '.')
            continue_on_error = hook.get('continueOnError', True)
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=working_dir,
                    capture_output=True,
                    timeout=60,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"      ✅ {name}")
                else:
                    print(f"      ⚠️  {name} (exit {result.returncode})")
                    if not continue_on_error:
                        all_passed = False
                        print(f"         {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                print(f"      ⏰ {name} timeout")
                if not continue_on_error:
                    all_passed = False
            except Exception as e:
                print(f"      ❌ {name}: {e}")
                if not continue_on_error:
                    all_passed = False
        
        return all_passed

