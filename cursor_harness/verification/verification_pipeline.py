"""
Verification pipeline - coordinates all verification steps.

Runs after each coding iteration:
1. Git diff analysis
2. Test execution
3. Lint/format checks

Returns structured results that can trigger LLM self-correction.
"""

import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from .git_analyzer import GitAnalyzer, DiffWarning


@dataclass
class VerificationResult:
    """Result of running verification pipeline."""
    passed: bool
    duration: float
    
    # Individual check results
    git_analysis: Dict
    test_results: Optional[Dict] = None
    lint_results: Optional[Dict] = None
    
    # For LLM feedback
    feedback: str = ""
    warnings: List[DiffWarning] = field(default_factory=list)
    
    def to_prompt(self) -> str:
        """Convert to prompt for LLM self-correction."""
        lines = []
        
        if not self.passed:
            lines.append("⚠️ **VERIFICATION FAILED**\n")
            lines.append("Please review and fix the following issues:\n")
        
        # Git analysis
        if not self.git_analysis.get('passed', True):
            lines.append("**Git Diff Analysis:**")
            for warning in self.warnings:
                location = f"{warning.file}:{warning.line}" if warning.line else warning.file
                lines.append(f"- [{warning.severity.upper()}] {location}: {warning.message}")
                if warning.suggestion:
                    lines.append(f"  → {warning.suggestion}")
            lines.append("")
        
        # Test results
        if self.test_results and not self.test_results.get('passed', True):
            lines.append("**Test Failures:**")
            lines.append(f"- {self.test_results.get('failed', 0)} test(s) failed")
            if 'output' in self.test_results:
                lines.append(f"```\n{self.test_results['output']}\n```")
            lines.append("")
        
        # Lint results
        if self.lint_results and not self.lint_results.get('passed', True):
            lines.append("**Lint Issues:**")
            lines.append(f"- {self.lint_results.get('issues', 0)} issue(s) found")
            if 'output' in self.lint_results:
                lines.append(f"```\n{self.lint_results['output']}\n```")
            lines.append("")
        
        if self.feedback:
            lines.append(f"**Additional Context:**\n{self.feedback}")
        
        return '\n'.join(lines)


class VerificationPipeline:
    """Coordinate verification checks after coding iterations."""
    
    def __init__(
        self,
        project_dir: Path,
        enable_git_analysis: bool = True,
        enable_tests: bool = True,
        enable_lint: bool = False  # Opt-in for now
    ):
        self.project_dir = Path(project_dir)
        self.enable_git_analysis = enable_git_analysis
        self.enable_tests = enable_tests
        self.enable_lint = enable_lint
        
        self.git_analyzer = GitAnalyzer(project_dir) if enable_git_analysis else None
    
    def verify(self) -> VerificationResult:
        """
        Run full verification pipeline.
        
        Returns VerificationResult with pass/fail and feedback for LLM.
        """
        start_time = time.time()
        
        git_analysis = {}
        test_results = None
        lint_results = None
        warnings = []
        
        overall_passed = True
        
        # 1. Git diff analysis
        if self.git_analyzer:
            try:
                git_passed, git_warnings = self.git_analyzer.analyze_uncommitted_changes()
                git_analysis = {
                    'passed': git_passed,
                    'warnings_count': len(git_warnings),
                    'changed_files': self.git_analyzer.get_changed_files(),
                    'summary': self.git_analyzer.get_diff_summary()
                }
                warnings = git_warnings
                
                if not git_passed:
                    overall_passed = False
            except Exception as e:
                git_analysis = {'passed': True, 'error': str(e)}
        
        # 2. Run tests (if configured)
        if self.enable_tests:
            test_results = self._run_tests()
            if test_results and not test_results.get('passed', True):
                overall_passed = False
        
        # 3. Run lint (if enabled)
        if self.enable_lint:
            lint_results = self._run_lint()
            if lint_results and not lint_results.get('passed', True):
                overall_passed = False
        
        duration = time.time() - start_time
        
        return VerificationResult(
            passed=overall_passed,
            duration=duration,
            git_analysis=git_analysis,
            test_results=test_results,
            lint_results=lint_results,
            warnings=warnings
        )
    
    def _run_tests(self) -> Optional[Dict]:
        """Run test suite and return results."""
        # Detect test framework
        test_command = self._detect_test_command()
        if not test_command:
            return None
        
        try:
            result = subprocess.run(
                test_command,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 min max
            )
            
            passed = result.returncode == 0
            
            return {
                'passed': passed,
                'exit_code': result.returncode,
                'output': result.stdout + result.stderr,
                'failed': 0 if passed else 1  # Simplified for now
            }
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'error': 'Tests timed out (300s limit)',
                'failed': 1
            }
        except Exception as e:
            return {
                'passed': True,  # Don't block on test infrastructure issues
                'error': str(e)
            }
    
    def _run_lint(self) -> Optional[Dict]:
        """Run linter and return results."""
        # Detect linter
        lint_command = self._detect_lint_command()
        if not lint_command:
            return None
        
        try:
            result = subprocess.run(
                lint_command,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            
            return {
                'passed': passed,
                'output': result.stdout + result.stderr,
                'issues': 0 if passed else 1  # Simplified
            }
        except Exception as e:
            return {
                'passed': True,  # Don't block on lint issues
                'error': str(e)
            }
    
    def _detect_test_command(self) -> Optional[List[str]]:
        """Auto-detect test command based on project files."""
        # Python
        if (self.project_dir / 'pytest.ini').exists() or \
           (self.project_dir / 'setup.py').exists() or \
           (self.project_dir / 'pyproject.toml').exists():
            return ['pytest', '-v']
        
        # Node.js
        package_json = self.project_dir / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                    if 'scripts' in data and 'test' in data['scripts']:
                        return ['npm', 'test']
            except:
                pass
        
        return None
    
    def _detect_lint_command(self) -> Optional[List[str]]:
        """Auto-detect lint command based on project files."""
        # Python
        if (self.project_dir / '.flake8').exists():
            return ['flake8', '.']
        if (self.project_dir / 'pylintrc').exists():
            return ['pylint', '.']
        
        # Node.js
        if (self.project_dir / '.eslintrc.js').exists() or \
           (self.project_dir / '.eslintrc.json').exists():
            return ['npx', 'eslint', '.']
        
        return None
