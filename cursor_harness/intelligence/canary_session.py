"""
Canary session system for parallel testing.

Runs experimental changes in isolated sessions before applying to main flow.
Compares outputs, detects regressions, auto-validates changes.
"""

import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import difflib


@dataclass
class CanaryResult:
    """Result from a canary session."""
    canary_id: str
    timestamp: str
    control_output: str
    canary_output: str
    control_duration: float
    canary_duration: float
    diff_score: float  # 0.0 = identical, 1.0 = completely different
    passed: bool
    regression_detected: bool
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'CanaryResult':
        return CanaryResult(**data)


class CanarySession:
    """
    Manages canary testing sessions.
    
    Runs same task in two parallel environments:
    - Control: Current stable version
    - Canary: Experimental changes
    
    Compares outputs and detects regressions.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize canary session manager.
        
        Args:
            project_dir: Project directory
        """
        self.project_dir = Path(project_dir)
        self.canary_dir = self.project_dir / ".cursor" / "canary"
        self.canary_dir.mkdir(parents=True, exist_ok=True)
        
        self.results_file = self.canary_dir / "results.json"
        self.results: List[CanaryResult] = []
        self._load_results()
    
    def run_canary_test(
        self,
        task_description: str,
        control_branch: str = "main",
        canary_branch: str = "HEAD",
        timeout_seconds: int = 300
    ) -> CanaryResult:
        """
        Run a canary test comparing two git branches/commits.
        
        Args:
            task_description: Task to execute in both sessions
            control_branch: Git ref for control (stable) version
            canary_branch: Git ref for canary (experimental) version
            timeout_seconds: Max execution time per session
        
        Returns:
            CanaryResult with comparison
        """
        canary_id = self._generate_canary_id(task_description, control_branch, canary_branch)
        
        # Create isolated workspaces
        control_dir = self.canary_dir / f"{canary_id}_control"
        canary_dir = self.canary_dir / f"{canary_id}_canary"
        
        try:
            # Clone to control workspace
            self._checkout_to_workspace(control_branch, control_dir)
            
            # Clone to canary workspace
            self._checkout_to_workspace(canary_branch, canary_dir)
            
            # Run task in control
            import time
            control_start = time.time()
            control_output = self._run_task(control_dir, task_description, timeout_seconds)
            control_duration = time.time() - control_start
            
            # Run task in canary
            canary_start = time.time()
            canary_output = self._run_task(canary_dir, task_description, timeout_seconds)
            canary_duration = time.time() - canary_start
            
            # Compare outputs
            diff_score = self._calculate_diff_score(control_output, canary_output)
            
            # Detect regressions
            regression = self._detect_regression(
                control_output, canary_output,
                control_duration, canary_duration,
                diff_score
            )
            
            # Determine pass/fail
            passed = not regression and diff_score < 0.3  # <30% difference = pass
            
            result = CanaryResult(
                canary_id=canary_id,
                timestamp=datetime.utcnow().isoformat(),
                control_output=control_output,
                canary_output=canary_output,
                control_duration=control_duration,
                canary_duration=canary_duration,
                diff_score=diff_score,
                passed=passed,
                regression_detected=regression
            )
            
            self.results.append(result)
            self._save_results()
            
            return result
            
        finally:
            # Cleanup workspaces
            self._cleanup_workspace(control_dir)
            self._cleanup_workspace(canary_dir)
    
    def _generate_canary_id(self, task: str, control: str, canary: str) -> str:
        """Generate unique canary ID."""
        content = f"{task}_{control}_{canary}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _checkout_to_workspace(self, git_ref: str, workspace: Path):
        """Checkout git ref to isolated workspace."""
        workspace.mkdir(parents=True, exist_ok=True)
        
        try:
            # Use git worktree for lightweight checkout
            subprocess.run(
                ['git', 'worktree', 'add', str(workspace), git_ref],
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            # Fallback: manual clone
            subprocess.run(
                ['git', 'clone', str(self.project_dir), str(workspace)],
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'checkout', git_ref],
                cwd=workspace,
                check=True,
                capture_output=True
            )
    
    def _run_task(self, workspace: Path, task: str, timeout: int) -> str:
        """
        Execute task in workspace and capture output.
        
        For cursor-harness, this would invoke the harness in the workspace.
        For now, returns a mock execution result.
        """
        # In real implementation, this would:
        # 1. Create a spec file with the task
        # 2. Run cursor-harness in the workspace
        # 3. Capture all output (files created, test results, etc.)
        # 4. Return serialized state for comparison
        
        # Mock implementation
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-1'],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _calculate_diff_score(self, control: str, canary: str) -> float:
        """
        Calculate similarity score between outputs.
        
        Returns:
            0.0 = identical, 1.0 = completely different
        """
        if control == canary:
            return 0.0
        
        # Use difflib sequence matcher
        matcher = difflib.SequenceMatcher(None, control, canary)
        similarity = matcher.ratio()  # 0.0 to 1.0, higher = more similar
        
        return 1.0 - similarity  # Invert to get difference score
    
    def _detect_regression(
        self,
        control_output: str,
        canary_output: str,
        control_duration: float,
        canary_duration: float,
        diff_score: float
    ) -> bool:
        """
        Detect if canary shows regression vs control.
        
        Regressions:
        - ERROR/FAIL in canary but not control
        - Significantly slower (>2x duration)
        - High diff score on critical outputs
        """
        # Check for new errors
        control_has_error = 'ERROR' in control_output or 'FAIL' in control_output
        canary_has_error = 'ERROR' in canary_output or 'FAIL' in canary_output
        
        if canary_has_error and not control_has_error:
            return True
        
        # Check for significant slowdown
        if canary_duration > control_duration * 2.0 and control_duration > 1.0:
            return True
        
        # High diff score might indicate regression
        if diff_score > 0.7:
            return True
        
        return False
    
    def _cleanup_workspace(self, workspace: Path):
        """Clean up canary workspace."""
        if not workspace.exists():
            return
        
        try:
            # Remove git worktree
            subprocess.run(
                ['git', 'worktree', 'remove', str(workspace), '--force'],
                cwd=self.project_dir,
                capture_output=True
            )
        except:
            pass
        
        # Fallback: manual cleanup
        import shutil
        try:
            shutil.rmtree(workspace)
        except:
            pass
    
    def get_recent_results(self, limit: int = 10) -> List[CanaryResult]:
        """Get recent canary test results."""
        return self.results[-limit:]
    
    def get_pass_rate(self) -> float:
        """Calculate overall canary pass rate."""
        if not self.results:
            return 0.0
        
        passed = sum(1 for r in self.results if r.passed)
        return passed / len(self.results)
    
    def get_stats(self) -> Dict:
        """Get canary testing statistics."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        regressions = sum(1 for r in self.results if r.regression_detected)
        
        avg_diff = sum(r.diff_score for r in self.results) / total if total > 0 else 0.0
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'regressions_detected': regressions,
            'pass_rate': passed / total if total > 0 else 0.0,
            'avg_diff_score': avg_diff
        }
    
    def _load_results(self):
        """Load results from disk."""
        if not self.results_file.exists():
            return
        
        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)
                self.results = [CanaryResult.from_dict(r) for r in data]
        except:
            pass
    
    def _save_results(self):
        """Save results to disk."""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(
                    [r.to_dict() for r in self.results],
                    f,
                    indent=2
                )
        except:
            pass
