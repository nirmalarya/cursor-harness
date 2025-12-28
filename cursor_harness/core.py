"""
cursor-harness v3.0 - Core Loop

Simple, reliable autonomous coding based on Anthropic's pattern.
Extended for production use (brownfield, backlog, etc).

Design: Keep it SIMPLE like Anthropic's demo (~300 lines)
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WorkItem:
    """A unit of work to implement."""
    id: str
    title: str
    description: str
    type: str  # feature, enhancement, bugfix, pbi
    acceptance_criteria: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "acceptance_criteria": self.acceptance_criteria
        }


@dataclass
class ExecutionResult:
    """Result of executing a work item."""
    success: bool
    output: str
    duration: float
    error: Optional[str] = None


class CursorHarness:
    """
    Simple autonomous coding harness.
    
    Inspired by Anthropic's demo, but production-ready:
    - Supports multiple modes (greenfield, enhancement, backlog)
    - Self-healing infrastructure
    - Real validation (tests, E2E, security)
    - Loop detection
    """
    
    def __init__(
        self,
        project_dir: Path,
        mode: str,
        spec_file: Optional[Path] = None,
        timeout_minutes: int = 60
    ):
        self.project_dir = Path(project_dir).resolve()
        self.mode = mode  # greenfield, enhancement, bugfix, backlog
        self.spec_file = spec_file
        self.timeout = timeout_minutes * 60
        
        # State
        self.state_dir = self.project_dir / ".cursor"
        self.state_dir.mkdir(exist_ok=True, parents=True)
        
        self.start_time = time.time()
        self.iteration = 0
        self.failure_counts = {}  # Track failures per work item
        self.max_retries = 3
        
        # Track if this is first session (initializer) or coding session
        self.is_first_session = not (self.project_dir / "feature_list.json").exists()
    
    def run(self) -> bool:
        """
        Main autonomous loop.
        
        Returns:
            True if completed successfully, False otherwise
        """
        
        print(f"\n{'='*60}")
        print(f"🚀 cursor-harness v3.0")
        print(f"{'='*60}")
        print(f"Mode: {self.mode}")
        print(f"Project: {self.project_dir}")
        print(f"{'='*60}\n")
        
        try:
            # 1. Setup (once)
            self._setup()
            
            # 2. Main work loop (Anthropic's session pattern)
            if self.is_first_session:
                # Session 1: INITIALIZER
                print(f"\n{'─'*60}")
                print("📋 Session 1: INITIALIZER")
                print(f"{'─'*60}")
                
                success = self._run_initializer_session()
                
                if not success:
                    print("\n❌ Initializer session failed!")
                    return False
                
                print("\n✅ Environment initialized!")
                print("   Created: feature_list.json, init.sh, cursor-progress.txt, git repo")
                
                # Mark first session complete
                self.is_first_session = False
            
            # Sessions 2-N: CODING (incremental progress)
            session = 1 if not self.is_first_session else 2
            max_sessions = 100  # Safety limit
            
            while session <= max_sessions:
                # Check timeout
                if time.time() - self.start_time > self.timeout:
                    print(f"\n⏰ Timeout reached ({self.timeout/60:.0f} minutes)")
                    return False
                
                # Check if complete
                if self._is_complete():
                    print(f"\n✅ All features complete!")
                    break
                
                # Run coding session
                print(f"\n{'─'*60}")
                print(f"📋 Session {session}: CODING")
                print(f"{'─'*60}")
                
                success = self._run_coding_session()
                
                if success:
                    print(f"✅ Session {session} complete")
                else:
                    print(f"⚠️  Session {session} made no progress")
                
                session += 1
            
            # 3. Final validation
            print(f"\n{'='*60}")
            print("🔍 Final Validation")
            print(f"{'='*60}")
            
            final_valid = self._final_validation()
            
            if final_valid:
                print(f"\n🎉 Project complete! ({self.iteration} iterations)")
                return True
            else:
                print(f"\n⚠️  Final validation failed")
                return False
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _setup(self):
        """One-time setup before main loop."""
        print("🔧 Setup...")
        
        # 1. Validate project directory
        if not self.project_dir.exists():
            if self.mode == "greenfield":
                print(f"   Creating project directory...")
                self.project_dir.mkdir(parents=True)
            else:
                raise ValueError(f"Project directory does not exist: {self.project_dir}")
        
        # 2. Initialize git if needed
        git_dir = self.project_dir / ".git"
        if not git_dir.exists():
            print(f"   Initializing git...")
            subprocess.run(
                ["git", "init"],
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "cursor-harness"],
                cwd=self.project_dir,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "cursor-harness@local"],
                cwd=self.project_dir,
                capture_output=True
            )
        
        # 3. Self-healing infrastructure
        from .infra.healer import InfrastructureHealer
        healer = InfrastructureHealer(self.project_dir)
        healer.heal()
        
        # 4. Load mode-specific adapter
        self._load_mode_adapter()
        
        print("✅ Setup complete\n")
    
    def _load_mode_adapter(self):
        """Load the appropriate mode adapter."""
        from .modes.greenfield import GreenfieldMode
        
        if self.mode == "greenfield":
            self.mode_adapter = GreenfieldMode(self.project_dir)
            self.mode_adapter.initialize()
            print(f"   Mode: Greenfield (feature_list.json)")
        else:
            # Other modes will be added later
            self.mode_adapter = None
            print(f"   Mode: {self.mode} (not implemented yet)")
    
    def _get_next_work(self) -> Optional[WorkItem]:
        """Get next work item based on mode."""
        
        if self.mode == "greenfield" and self.mode_adapter:
            feature = self.mode_adapter.get_next_feature()
            if feature:
                return WorkItem(
                    id=feature.id,
                    title=feature.title,
                    description=feature.description,
                    type="feature"
                )
        
        return None
    
    def _is_complete(self) -> bool:
        """Check if all work is complete."""
        
        if self.mode == "greenfield" and self.mode_adapter:
            return self.mode_adapter.is_complete()
        
        # For other modes, use iteration limit for now
        return self.iteration >= 10
    
    def _run_initializer_session(self) -> bool:
        """Run the initializer session (Anthropic's pattern)."""
        
        prompt = self._build_prompt()
        
        # Execute with Claude
        return self._execute_session(prompt, "initializer")
    
    def _run_coding_session(self) -> bool:
        """Run a coding session (Anthropic's pattern)."""
        
        prompt = self._build_prompt()
        
        # Execute with Claude
        return self._execute_session(prompt, "coding")
    
    def _execute_session(self, prompt: str, session_type: str) -> bool:
        """Execute a session using Cursor's Claude."""
        
        try:
            from .executor.cursor_executor import CursorExecutor
            
            if not hasattr(self, '_executor'):
                self._executor = CursorExecutor(self.project_dir)
            
            return self._executor.execute(prompt)
            
        except ImportError:
            print(f"   ℹ️  Install: pip install anthropic")
            return False
        except ValueError as e:
            print(f"   ℹ️  {e}")
            return False
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            return False
    
    def _validate_work_item(self, work_item: WorkItem) -> bool:
        """Validate that work item was completed."""
        
        # Check git for changes
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            has_changes = len(result.stdout.strip()) > 0
            
            if has_changes:
                # Commit changes
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.project_dir,
                    capture_output=True,
                    timeout=5
                )
                subprocess.run(
                    ["git", "commit", "-m", f"feat: {work_item.title}"],
                    cwd=self.project_dir,
                    capture_output=True,
                    timeout=5
                )
                print(f"   ✅ Committed changes")
                return True
            else:
                print(f"   ⚠️  No changes detected")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Validation error: {e}")
            return False
    
    def _build_prompt(self, work_item: WorkItem = None) -> str:
        """
        Build prompt based on Anthropic's two-prompt pattern.
        
        Returns:
            Initializer prompt (first session) or Coding prompt (subsequent)
        """
        from pathlib import Path
        
        prompts_dir = Path(__file__).parent / "prompts"
        
        if self.is_first_session:
            # INITIALIZER session
            initializer_prompt = (prompts_dir / "initializer.md").read_text()
            
            # Add project spec
            if self.spec_file and self.spec_file.exists():
                spec_content = self.spec_file.read_text()
                return f"{initializer_prompt}\n\n---\n\n## Project Specification\n\n{spec_content}"
            
            return initializer_prompt
        else:
            # CODING session
            return (prompts_dir / "coding.md").read_text()
    
    def _mark_complete(self, work_item: WorkItem):
        """Mark work item as complete."""
        
        # Update mode adapter
        if self.mode == "greenfield" and self.mode_adapter:
            self.mode_adapter.mark_passing(work_item.id)
        
        # Save completion record
        completion_file = self.state_dir / f"completed_{work_item.id}.json"
        completion_file.write_text(json.dumps({
            "id": work_item.id,
            "title": work_item.title,
            "completed_at": datetime.now().isoformat(),
            "iteration": self.iteration
        }, indent=2))
    
    def _handle_failure(self, work_item: WorkItem):
        """Handle work item failure."""
        
        # Update mode adapter
        if self.mode == "greenfield" and self.mode_adapter:
            self.mode_adapter.mark_failing(work_item.id)
        
        # Save failure record
        failure_file = self.state_dir / f"failed_{work_item.id}.json"
        failure_file.write_text(json.dumps({
            "id": work_item.id,
            "title": work_item.title,
            "failed_at": datetime.now().isoformat(),
            "iteration": self.iteration
        }, indent=2))
    
    def _final_validation(self) -> bool:
        """Run final validation checks."""
        
        from .validators.test_runner import TestRunner
        from .validators.secrets_scanner import SecretsScanner
        
        all_passed = True
        
        # 1. Tests
        print("\n1. Running tests...")
        test_runner = TestRunner(self.project_dir)
        test_result = test_runner.run_tests()
        if test_result.passed:
            print(f"   ✅ Tests passed")
        else:
            print(f"   ❌ Tests failed")
            all_passed = False
        
        # 2. Secrets
        print("\n2. Security scan...")
        scanner = SecretsScanner(self.project_dir)
        secrets = scanner.scan()
        if not secrets:
            print(f"   ✅ No secrets exposed")
        else:
            print(f"   ❌ Found {len(secrets)} potential secrets!")
            for s in secrets[:5]:
                print(f"      {s.file}:{s.line} - {s.type}")
            all_passed = False
        
        return all_passed


def main():
    """Simple CLI for testing."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python core.py <mode> <project_dir> [spec_file]")
        print("Modes: greenfield, enhancement, bugfix, backlog")
        sys.exit(1)
    
    mode = sys.argv[1]
    project_dir = Path(sys.argv[2])
    spec_file = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    
    harness = CursorHarness(
        project_dir=project_dir,
        mode=mode,
        spec_file=spec_file
    )
    
    success = harness.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

