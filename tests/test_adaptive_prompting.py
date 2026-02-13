"""Tests for adaptive prompting and pattern learning."""

import tempfile
from pathlib import Path

from cursor_harness.intelligence.pattern_db import PatternDatabase, ErrorPattern
from cursor_harness.intelligence.adaptive_prompter import AdaptivePrompter


def test_pattern_recording():
    """Test recording and retrieving error patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        db = PatternDatabase(project_dir)
        
        # Record an error
        pattern_id = db.record_error(
            error_type="test_failure",
            error_message="AssertionError: Expected 5, got 3 at line 42",
            files_affected=["test_math.py"]
        )
        
        assert pattern_id is not None
        assert len(db.patterns) == 1
        
        # Record same error again
        pattern_id2 = db.record_error(
            error_type="test_failure",
            error_message="AssertionError: Expected 5, got 3 at line 45",  # Different line
            files_affected=["test_math.py"]
        )
        
        # Should be same pattern (normalized)
        assert pattern_id2 == pattern_id
        assert len(db.patterns) == 1
        assert db.patterns[pattern_id].occurrence_count == 2


def test_pattern_resolution():
    """Test recording successful and failed resolutions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        db = PatternDatabase(project_dir)
        
        pattern_id = db.record_error(
            error_type="lint_error",
            error_message="undefined variable 'foo'",
            files_affected=["main.py"]
        )
        
        # Record successful resolution
        db.record_resolution(
            pattern_id=pattern_id,
            success=True,
            fix_description="Added variable declaration at top of function"
        )
        
        pattern = db.patterns[pattern_id]
        assert pattern.resolution_count == 1
        assert pattern.success_rate == 1.0
        assert len(pattern.successful_fixes) == 1
        
        # Record another occurrence and failed resolution
        db.record_error(
            error_type="lint_error",
            error_message="undefined variable 'foo'",
            files_affected=["main.py"]
        )
        
        db.record_resolution(
            pattern_id=pattern_id,
            success=False,
            fix_description="Tried to use global declaration, didn't work"
        )
        
        pattern = db.patterns[pattern_id]
        assert pattern.occurrence_count == 2
        assert pattern.resolution_count == 1  # Still only 1 successful
        assert pattern.success_rate == 0.5  # 1/2
        assert len(pattern.failed_fixes) == 1


def test_adaptive_prompter_augmentation():
    """Test prompt augmentation with learned patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create prompter and record some patterns
        prompter = AdaptivePrompter(project_dir, enabled=True)
        
        # Record a pattern
        pattern_id = prompter.record_error(
            error_type="test_failure",
            error_message="TypeError: cannot concatenate str and int",
            files_affected=["utils.py"]
        )
        
        prompter.record_resolution(
            pattern_id=pattern_id,
            success=True,
            fix_description="Added str() conversion before concatenation"
        )
        
        # Augment a prompt
        base_prompt = "## Your Task\n\nImplement a new feature."
        
        augmented = prompter.augment_prompt(base_prompt)
        
        # Should contain pattern injection
        assert "Learned Patterns" in augmented
        assert "test_failure" in augmented
        assert base_prompt in augmented


def test_pattern_persistence():
    """Test that patterns persist across database instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create first database and record pattern
        db1 = PatternDatabase(project_dir)
        pattern_id = db1.record_error(
            error_type="verification_failure",
            error_message="Large deletion detected in important_file.py",
            files_affected=["important_file.py"]
        )
        
        # Create new database instance (simulating new session)
        db2 = PatternDatabase(project_dir)
        
        # Should load persisted pattern
        assert len(db2.patterns) == 1
        assert pattern_id in db2.patterns
        assert db2.patterns[pattern_id].error_type == "verification_failure"


if __name__ == '__main__':
    test_pattern_recording()
    test_pattern_resolution()
    test_adaptive_prompter_augmentation()
    test_pattern_persistence()
    print("✅ All adaptive prompting tests passed!")
