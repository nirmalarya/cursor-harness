"""Test execution validator."""

import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class TestResult:
    passed: bool
    total: int = 0
    passing: int = 0
    coverage: float = 0.0
    output: str = ""


class TestRunner:
    """Run and validate tests."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def run_tests(self) -> TestResult:
        """Run project tests."""
        
        # Detect test framework
        if (self.project_dir / "package.json").exists():
            return self._run_npm_tests()
        elif (self.project_dir / "pytest.ini").exists():
            return self._run_pytest()
        elif (self.project_dir / "go.mod").exists():
            return self._run_go_tests()
        else:
            return TestResult(passed=True, output="No tests found")
    
    def _run_npm_tests(self) -> TestResult:
        """Run npm test."""
        try:
            result = subprocess.run(
                ["npm", "test"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=300,
                text=True
            )
            return TestResult(
                passed=result.returncode == 0,
                output=result.stdout + result.stderr
            )
        except Exception as e:
            return TestResult(passed=False, output=str(e))
    
    def _run_pytest(self) -> TestResult:
        """Run pytest."""
        try:
            result = subprocess.run(
                ["pytest", "--cov", "--cov-report=term"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=300,
                text=True
            )
            return TestResult(
                passed=result.returncode == 0,
                output=result.stdout + result.stderr
            )
        except Exception as e:
            return TestResult(passed=False, output=str(e))
    
    def _run_go_tests(self) -> TestResult:
        """Run go test."""
        try:
            result = subprocess.run(
                ["go", "test", "./...", "-cover"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=300,
                text=True
            )
            return TestResult(
                passed=result.returncode == 0,
                output=result.stdout + result.stderr
            )
        except Exception as e:
            return TestResult(passed=False, output=str(e))

