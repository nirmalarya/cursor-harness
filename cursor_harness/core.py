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

from . import __version__


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
        timeout_minutes: int = 60,
        model: str = "sonnet-4.5"
    ):
        self.project_dir = Path(project_dir).resolve()
        self.mode = mode  # greenfield, enhancement, bugfix, backlog
        self.spec_file = spec_file
        self.timeout = timeout_minutes * 60
        self.model = model
        
        # State
        self.state_dir = self.project_dir / ".cursor"
        self.state_dir.mkdir(exist_ok=True, parents=True)
        
        self.start_time = time.time()
        self.iteration = 0
        self.failure_counts = {}  # Track failures per work item
        self.max_retries = 3
    
        # Track if this is first session (initializer) or coding session
        feature_list_exists = (self.project_dir / "feature_list.json").exists()
        self.is_first_session = not feature_list_exists
        
        # Check if continuation mode (existing feature list is large)
        self.is_continuation = False
        if feature_list_exists:
            try:
                import json
                with open(self.project_dir / "feature_list.json") as f:
                    features = json.load(f)
                # If >50 features, use continuation mode
                if len(features) > 50:
                    self.is_continuation = True
                    print(f"   ℹ️  Continuation mode ({len(features)} features)")
            except:
                pass
    
    def run(self) -> bool:
        """
        Main autonomous loop.
        
        Returns:
            True if completed successfully, False otherwise
        """
        
        print(f"\n{'='*60}")
        print(f"🚀 cursor-harness v{__version__}")
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
                    # cursor-agent runs hooks automatically (no need to call them!)
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

        # 0. Automatic process cleanup (v3.2.0+)
        # cursor-agent processes are now tracked globally and cleaned up automatically:
        # - On normal program exit (atexit)
        # - On interrupt signals (SIGINT, SIGTERM)
        # - On exceptions (try/finally in executor)
        # No more manual pkill -9 needed!
        print("   ✅ Automatic process cleanup enabled")

        # 1. Validate project directory
        if not self.project_dir.exists():
            if self.mode == "greenfield":
                print(f"   Creating project directory...")
                self.project_dir.mkdir(parents=True)
            else:
                raise ValueError(f"Project directory does not exist: {self.project_dir}")
        
        # 2. Initialize git if needed (greenfield only)
        git_dir = self.project_dir / ".git"
        if not git_dir.exists() and self.mode == "greenfield":
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
        
        # 3. Self-healing infrastructure (brownfield modes only)
        if self.mode in ["enhancement", "enhance", "backlog"]:
            from .infra.healer import InfrastructureHealer
            healer = InfrastructureHealer(self.project_dir)
            healer.heal()
        
        # 4. Setup hooks (automatic validation!)
        from .hooks import HooksManager
        hooks_manager = HooksManager(self.project_dir)
        hooks_manager.setup_default_hooks()
        self.hooks_manager = hooks_manager

        # 4.5. Setup MCP servers (browser automation + Azure DevOps)
        from .setup_mcp import MCPServerSetup
        mcp_setup = MCPServerSetup(self.project_dir, self.mode)

        if self.mode == "backlog":
            # Setup Azure DevOps MCP for backlog mode
            mcp_setup.setup(
                ado_org=getattr(self, 'ado_org', None),
                ado_project=getattr(self, 'ado_project', None)
            )
        else:
            # Setup browser automation MCP for greenfield/enhancement
            mcp_setup.setup()

        # Store browser tools for prompts
        self.browser_tools = mcp_setup.get_browser_tools()

        # 5. Backlog mode: Prepare Azure DevOps state
        if self.mode == "backlog":
            self._setup_backlog_mode()
        
        print(f"   Mode: {self.mode}")
        print("✅ Setup complete\n")
    
    def _setup_backlog_mode(self):
        """Setup for backlog mode - create backlog state for agent."""
        print(f"   Setting up Azure DevOps backlog...")
        
        # Agent will use MCP to fetch PBIs
        # We just create the state file location
        from .integrations.azure_devops import AzureDevOpsIntegration
        
        # Parse org/project from CLI args (already set elsewhere)
        org = getattr(self, 'ado_org', 'unknown')
        project = getattr(self, 'ado_project', 'unknown')
        
        ado = AzureDevOpsIntegration(org, project, self.project_dir)
        
        # Save empty state - agent will populate using MCP
        ado.save_backlog_state([])
        
        print(f"   Backlog state file created")
    
    
    def _is_complete(self) -> bool:
        """Check if all features are complete (Anthropic's pattern)."""

        # Check feature_list.json
        feature_list = self.project_dir / "feature_list.json"
        if not feature_list.exists():
            return False

        try:
            import json
            with open(feature_list) as f:
                features = json.load(f)

            if not features:
                return True

            # All features must be passing
            return all(f.get('passes', False) for f in features)
        except:
            return False

    def _get_current_work_item(self) -> dict:
        """
        Get the work item being implemented this session.

        Returns the first non-passing feature from feature_list.json.
        This is what the agent should be working on.

        Used for E2E verification.
        """
        feature_list = self.project_dir / "feature_list.json"
        if not feature_list.exists():
            return None

        try:
            import json
            with open(feature_list) as f:
                features = json.load(f)

            # Find first non-passing feature
            for feature in features:
                if not feature.get('passes', False):
                    return feature
        except:
            pass

        return None
    
    def _run_initializer_session(self) -> bool:
        """Run the initializer session (Anthropic's pattern)."""
        
        prompt = self._build_prompt()
        
        # Execute with Claude
        return self._execute_session(prompt, "initializer")
    
    def _run_coding_session(self) -> bool:
        """Run a coding session (Anthropic's pattern + E2E verification)."""

        # Get current work item for E2E verification
        work_item = self._get_current_work_item()

        # Build and execute prompt
        prompt = self._build_prompt()
        success = self._execute_session(prompt, "coding")

        if not success:
            return False

        # Production enhancement: Verify E2E testing was done
        # Only for user-facing modes (greenfield, enhancement)
        if self.mode in ['greenfield', 'enhancement'] and work_item:
            from .validators.e2e_verifier import E2EVerifier
            verifier = E2EVerifier(self.project_dir)

            result = verifier.verify(work_item)

            if not result.passed:
                print(f"\n   ⚠️  E2E Verification Failed: {result.reason}")
                print(f"   💡 Tip: Agent must save Puppeteer screenshots to .cursor/verification/")
                print(f"   💡 See prompts for E2E testing requirements")
                return False
            else:
                print(f"   ✅ E2E verified: {result.reason}")

        return True
    
    def _execute_session(self, prompt: str, session_type: str) -> bool:
        """Execute a session using Cursor's Claude."""
        
        try:
            from .executor.cursor_executor import CursorExecutor
            from .loop_detector import LoopDetector
            
            # Create loop detector for this session
            loop_detector = LoopDetector(max_repeated_reads=5, session_timeout_minutes=60)
            
            if not hasattr(self, '_executor'):
                self._executor = CursorExecutor(self.project_dir, loop_detector, self.model)
            
            return self._executor.execute(prompt)
            
        except ImportError:
            print(f"\n   ℹ️  Install anthropic: pip install anthropic")
            print(f"   Or set ANTHROPIC_API_KEY environment variable")
            return False
        except ValueError as e:
            # cursor-agent not available
            print(f"\n❌ {e}")
            return False
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            return False
    
    
    def _build_prompt(self, work_item: WorkItem = None) -> str:
        """
        Build prompt based on Anthropic's two-prompt pattern + mode.
        
        Returns:
            Appropriate prompt for mode and session
        """
        from pathlib import Path
        
        prompts_dir = Path(__file__).parent / "prompts"
        
        # Select prompt based on mode and session
        if self.is_first_session:
            # INITIALIZER prompts
            if self.mode == "enhancement" or self.mode == "enhance":
                prompt_file = prompts_dir / "enhancement_initializer.md"
            elif self.mode == "backlog":
                prompt_file = prompts_dir / "backlog_initializer.md"
            else:  # greenfield
                prompt_file = prompts_dir / "initializer.md"
        else:
            # CODING prompts - use continuation mode for large projects
            if self.mode == "enhancement" or self.mode == "enhance":
                if self.is_continuation:
                    prompt_file = prompts_dir / "enhancement_continuation.md"
                else:
                    prompt_file = prompts_dir / "enhancement_coding.md"
            elif self.mode == "backlog":
                if self.is_continuation:
                    prompt_file = prompts_dir / "backlog_continuation.md"
                else:
                    prompt_file = prompts_dir / "backlog_coding.md"
            else:  # greenfield
                if self.is_continuation:
                    prompt_file = prompts_dir / "continuation_coding.md"
                else:
                    prompt_file = prompts_dir / "coding.md"
        
        prompt = prompt_file.read_text()

        # Replace template variables with actual MCP tools
        prompt = self._inject_mcp_tools(prompt)

        # Add system instructions (common to all)
        system_instructions = (prompts_dir / "system_instructions.md").read_text()
        prompt = f"{prompt}\n\n---\n\n{system_instructions}"

        # Add project spec for initializer
        if self.is_first_session and self.spec_file and self.spec_file.exists():
            spec_content = self.spec_file.read_text()
            prompt = f"{prompt}\n\n---\n\n## Project Specification\n\n{spec_content}"

        return prompt

    def _inject_mcp_tools(self, prompt: str) -> str:
        """
        Replace template variables with actual MCP tool names.

        Args:
            prompt: Prompt template with {{BROWSER_MCP_TOOLS}} placeholder

        Returns:
            Prompt with actual tool names injected
        """
        # Get browser tools (set during _setup())
        browser_tools = getattr(self, 'browser_tools', [])

        if browser_tools:
            # Generate tool documentation
            tool_type = "puppeteer" if "puppeteer_navigate" in browser_tools else "playwright"

            tools_doc = f"""Available {tool_type.capitalize()} MCP tools (auto-configured):
"""

            tool_descriptions = {
                "puppeteer_navigate": "Navigate to URL",
                "puppeteer_screenshot": "Capture screenshot of current page",
                "puppeteer_click": "Click element by selector",
                "puppeteer_fill": "Fill form input by selector",
                "puppeteer_select": "Select dropdown option",
                "puppeteer_hover": "Hover over element",
                "puppeteer_evaluate": "Execute JavaScript (use sparingly!)",
                "playwright_navigate": "Navigate to URL",
                "playwright_screenshot": "Capture screenshot of current page",
                "playwright_click": "Click element by selector",
                "playwright_fill": "Fill form input by selector",
                "playwright_type": "Type text into element"
            }

            for tool in browser_tools:
                desc = tool_descriptions.get(tool, "Browser automation tool")
                tools_doc += f"- `{tool}` - {desc}\n"

            # Replace placeholder
            prompt = prompt.replace("{{BROWSER_MCP_TOOLS}}", tools_doc.strip())
        else:
            # No browser tools configured - remove placeholder
            fallback = """⚠️  No browser automation MCP configured.
E2E testing will use project's existing test framework (npm run test:e2e, etc.)"""
            prompt = prompt.replace("{{BROWSER_MCP_TOOLS}}", fallback)

        return prompt
    
    
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

