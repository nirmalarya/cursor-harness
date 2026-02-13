"""Tests for Git diff analyzer."""

import subprocess
import tempfile
from pathlib import Path

from cursor_harness.verification.git_analyzer import GitAnalyzer, DiffWarning


def test_git_analyzer_no_changes():
    """Test analyzer with no uncommitted changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Init git repo
        subprocess.run(['git', 'init'], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=project_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=project_dir, check=True)
        
        # Create and commit a file
        (project_dir / 'test.txt').write_text('Hello world')
        subprocess.run(['git', 'add', '.'], cwd=project_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_dir, check=True, capture_output=True)
        
        # Analyze (should pass with no warnings)
        analyzer = GitAnalyzer(project_dir)
        passed, warnings = analyzer.analyze_uncommitted_changes()
        
        assert passed is True
        assert len(warnings) == 0


def test_git_analyzer_sensitive_pattern():
    """Test analyzer detects sensitive patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Init git repo
        subprocess.run(['git', 'init'], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=project_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=project_dir, check=True)
        
        # Create initial file
        (project_dir / 'config.py').write_text('# Config\n')
        subprocess.run(['git', 'add', '.'], cwd=project_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=project_dir, check=True, capture_output=True)
        
        # Add file with sensitive pattern
        (project_dir / 'config.py').write_text('# Config\napi_key = "sk-1234567890"\n')
        
        # Analyze (should fail with error)
        analyzer = GitAnalyzer(project_dir)
        passed, warnings = analyzer.analyze_uncommitted_changes()
        
        assert passed is False
        assert len(warnings) > 0
        assert any(w.severity == 'error' and 'api_key' in w.message.lower() for w in warnings)


def test_git_analyzer_get_changed_files():
    """Test getting list of changed files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Init git repo
        subprocess.run(['git', 'init'], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=project_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=project_dir, check=True)
        
        # Create and commit initial files
        (project_dir / 'file1.txt').write_text('Content 1')
        (project_dir / 'file2.txt').write_text('Content 2')
        subprocess.run(['git', 'add', '.'], cwd=project_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=project_dir, check=True, capture_output=True)
        
        # Modify one file
        (project_dir / 'file1.txt').write_text('Modified content')
        
        # Get changed files
        analyzer = GitAnalyzer(project_dir)
        changed = analyzer.get_changed_files()
        
        assert 'file1.txt' in changed
        assert 'file2.txt' not in changed


if __name__ == '__main__':
    test_git_analyzer_no_changes()
    test_git_analyzer_sensitive_pattern()
    test_git_analyzer_get_changed_files()
    print("✅ All tests passed!")
