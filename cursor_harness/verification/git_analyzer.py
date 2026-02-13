"""
Git diff analyzer for verification pipeline.

Detects problematic changes:
- Unintended modifications
- Large deletions
- Binary files
- Sensitive patterns
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DiffWarning:
    """A potential issue detected in git diff."""
    severity: str  # error, warning, info
    file: str
    line: Optional[int]
    message: str
    suggestion: Optional[str] = None


class GitAnalyzer:
    """Analyze git diffs for issues."""
    
    # Thresholds for warnings
    LARGE_DELETION_LINES = 100
    LARGE_FILE_LINES = 1000
    
    # Patterns that might indicate problems
    SENSITIVE_PATTERNS = [
        'password',
        'api_key',
        'secret',
        'token',
        'private_key'
    ]
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
    
    def analyze_uncommitted_changes(self) -> Tuple[bool, List[DiffWarning]]:
        """
        Analyze all uncommitted changes.
        
        Returns:
            (passed, warnings) - False if critical issues found
        """
        warnings = []
        
        # Get diff stats
        try:
            result = subprocess.run(
                ['git', 'diff', '--stat'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                warnings.append(DiffWarning(
                    severity='warning',
                    file='',
                    line=None,
                    message='Git diff failed - repo may not be initialized',
                    suggestion='Initialize git: git init'
                ))
                return True, warnings  # Don't block on git issues
        except subprocess.TimeoutExpired:
            warnings.append(DiffWarning(
                severity='warning',
                file='',
                line=None,
                message='Git diff timed out'
            ))
            return True, warnings
        
        if not result.stdout.strip():
            # No changes
            return True, warnings
        
        # Parse diff stat for file-level warnings
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    file_path = parts[0].strip()
                    stats = parts[1].strip()
                    
                    # Check for large deletions
                    if '-' in stats:
                        deletions = stats.count('-')
                        if deletions > 50:  # Visual indicator threshold
                            warnings.append(DiffWarning(
                                severity='warning',
                                file=file_path,
                                line=None,
                                message=f'Large deletion detected (~{deletions} lines)',
                                suggestion='Verify this deletion is intentional'
                            ))
        
        # Get full diff for content analysis
        try:
            result = subprocess.run(
                ['git', 'diff'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                diff_content = result.stdout
                
                # Check for binary files
                if 'Binary files' in diff_content:
                    for line in diff_content.split('\n'):
                        if line.startswith('Binary files'):
                            warnings.append(DiffWarning(
                                severity='info',
                                file=line.split(' ')[-1] if ' ' in line else '',
                                line=None,
                                message='Binary file modified',
                                suggestion='Verify binary changes are intentional'
                            ))
                
                # Check for sensitive patterns in added lines
                current_file = None
                line_num = 0
                
                for line in diff_content.split('\n'):
                    if line.startswith('diff --git'):
                        # Extract filename
                        parts = line.split(' ')
                        if len(parts) >= 4:
                            current_file = parts[3].lstrip('b/')
                        line_num = 0
                    elif line.startswith('@@'):
                        # Parse line number from hunk header
                        try:
                            parts = line.split(' ')
                            if len(parts) >= 3:
                                line_info = parts[2].lstrip('+').split(',')
                                line_num = int(line_info[0])
                        except:
                            pass
                    elif line.startswith('+') and not line.startswith('+++'):
                        line_num += 1
                        # Check added lines for sensitive patterns
                        line_lower = line.lower()
                        for pattern in self.SENSITIVE_PATTERNS:
                            if pattern in line_lower and '=' in line:
                                # Looks like an assignment
                                warnings.append(DiffWarning(
                                    severity='error',
                                    file=current_file or 'unknown',
                                    line=line_num,
                                    message=f'Possible sensitive data: {pattern}',
                                    suggestion='Use environment variables or secrets manager'
                                ))
        except subprocess.TimeoutExpired:
            warnings.append(DiffWarning(
                severity='warning',
                file='',
                line=None,
                message='Full diff analysis timed out'
            ))
        
        # Determine pass/fail
        has_errors = any(w.severity == 'error' for w in warnings)
        
        return not has_errors, warnings
    
    def get_changed_files(self) -> List[str]:
        """Get list of files with uncommitted changes."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        except:
            pass
        
        return []
    
    def get_diff_summary(self) -> str:
        """Get human-readable diff summary."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--stat'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return "No changes"
