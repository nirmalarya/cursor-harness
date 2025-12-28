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
        """
        Setup Cursor hooks (hooks.json + shell scripts).
        
        cursor-agent will run these automatically!
        """
        
        hooks_dir = self.project_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        
        # Cursor hooks.json format (from docs)
        hooks_config = {
            "version": 1,
            "hooks": {
                "afterFileEdit": [],
                "stop": []
            }
        }
        
        # Python project
        if (self.project_dir / "requirements.txt").exists():
            # After edit: run tests
            test_script = hooks_dir / "run-tests.sh"
            test_script.write_text("""#!/bin/bash
# Auto-run pytest after file edits
pytest --tb=short -x || true
exit 0
""")
            test_script.chmod(0o755)
            
            hooks_config["hooks"]["afterFileEdit"].append({
                "command": "./hooks/run-tests.sh"
            })
            
            # On stop: coverage check
            cov_script = hooks_dir / "coverage-check.sh"
            cov_script.write_text("""#!/bin/bash
# Run coverage on session stop
pytest --cov --cov-report=term-missing || true
exit 0
""")
            cov_script.chmod(0o755)
            
            hooks_config["hooks"]["stop"].append({
                "command": "./hooks/coverage-check.sh"
            })
        
        # TypeScript/JavaScript project
        if (self.project_dir / "package.json").exists():
            # After edit: eslint
            lint_script = hooks_dir / "eslint.sh"
            lint_script.write_text("""#!/bin/bash
# Auto-run eslint after file edits
npm run lint || true
exit 0
""")
            lint_script.chmod(0o755)
            
            hooks_config["hooks"]["afterFileEdit"].append({
                "command": "./hooks/eslint.sh"
            })
            
            # On stop: build
            build_script = hooks_dir / "build.sh"
            build_script.write_text("""#!/bin/bash
# Build on session stop
npm run build || true
exit 0
""")
            build_script.chmod(0o755)
            
            hooks_config["hooks"]["stop"].append({
                "command": "./hooks/build.sh"
            })
        
        # Go project
        if (self.project_dir / "go.mod").exists():
            # After edit: gofmt + go vet
            fmt_script = hooks_dir / "go-check.sh"
            fmt_script.write_text("""#!/bin/bash
# Auto-format and vet Go code
gofmt -w . || true
go vet ./... || true
exit 0
""")
            fmt_script.chmod(0o755)
            
            hooks_config["hooks"]["afterFileEdit"].append({
                "command": "./hooks/go-check.sh"
            })
            
            # On stop: tests
            test_script = hooks_dir / "go-test.sh"
            test_script.write_text("""#!/bin/bash
# Run Go tests on session stop
go test ./... || true
exit 0
""")
            test_script.chmod(0o755)
            
            hooks_config["hooks"]["stop"].append({
                "command": "./hooks/go-test.sh"
            })
        
        # Save hooks.json
        self.hooks_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.hooks_file, 'w') as f:
            json.dump(hooks_config, f, indent=2)
        
        hook_count = len(hooks_config["hooks"]["afterFileEdit"]) + len(hooks_config["hooks"]["stop"])
        print(f"   ✅ Hooks configured ({hook_count} total - cursor-agent will auto-run them)")
    
    def verify_hooks_setup(self) -> bool:
        """Verify hooks are set up correctly."""
        if self.hooks_file.exists():
            print(f"   ✅ Hooks configured at {self.hooks_file}")
            return True
        return False
    
    def run_hook_DEPRECATED(self, hook_type: str) -> bool:
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

