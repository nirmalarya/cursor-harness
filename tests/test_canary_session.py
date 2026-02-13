"""Tests for canary session system."""

import tempfile
from pathlib import Path
import subprocess

from cursor_harness.intelligence.canary_session import CanarySession, CanaryResult


def test_canary_result():
    """Test canary result creation."""
    result = CanaryResult(
        canary_id="test123",
        timestamp="2026-02-13T12:00:00",
        control_output="Success",
        canary_output="Success",
        control_duration=1.5,
        canary_duration=1.6,
        diff_score=0.0,
        passed=True,
        regression_detected=False
    )
    
    assert result.canary_id == "test123"
    assert result.passed is True
    assert result.regression_detected is False
    
    # Test serialization
    data = result.to_dict()
    restored = CanaryResult.from_dict(data)
    assert restored.canary_id == result.canary_id
    assert restored.diff_score == result.diff_score


def test_diff_score_calculation():
    """Test output difference scoring."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Init git repo
        subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=project_dir)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=project_dir)
        
        canary = CanarySession(project_dir)
        
        # Identical outputs
        score1 = canary._calculate_diff_score("Hello", "Hello")
        assert score1 == 0.0
        
        # Completely different
        score2 = canary._calculate_diff_score("ABC", "XYZ")
        assert score2 > 0.5
        
        # Similar but not identical
        score3 = canary._calculate_diff_score("Hello World", "Hello World!")
        assert 0.0 < score3 < 0.3


def test_regression_detection():
    """Test regression detection logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=project_dir)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=project_dir)
        
        canary = CanarySession(project_dir)
        
        # No regression: both pass
        reg1 = canary._detect_regression(
            "Success", "Success",
            1.0, 1.1, 0.05
        )
        assert reg1 is False
        
        # Regression: new error
        reg2 = canary._detect_regression(
            "Success", "ERROR: Failed",
            1.0, 1.1, 0.5
        )
        assert reg2 is True
        
        # Regression: significant slowdown
        reg3 = canary._detect_regression(
            "Success", "Success",
            2.0, 5.0, 0.0
        )
        assert reg3 is True
        
        # Regression: high diff score
        reg4 = canary._detect_regression(
            "Output A", "Completely different output",
            1.0, 1.0, 0.8
        )
        assert reg4 is True


def test_canary_stats():
    """Test statistics calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=project_dir)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=project_dir)
        
        canary = CanarySession(project_dir)
        
        # Add passing result
        canary.results.append(CanaryResult(
            canary_id="test1",
            timestamp="2026-02-13T12:00:00",
            control_output="OK",
            canary_output="OK",
            control_duration=1.0,
            canary_duration=1.0,
            diff_score=0.0,
            passed=True,
            regression_detected=False
        ))
        
        # Add failing result
        canary.results.append(CanaryResult(
            canary_id="test2",
            timestamp="2026-02-13T12:01:00",
            control_output="OK",
            canary_output="ERROR",
            control_duration=1.0,
            canary_duration=1.0,
            diff_score=0.8,
            passed=False,
            regression_detected=True
        ))
        
        stats = canary.get_stats()
        
        assert stats['total_tests'] == 2
        assert stats['passed'] == 1
        assert stats['failed'] == 1
        assert stats['regressions_detected'] == 1
        assert stats['pass_rate'] == 0.5


def test_persistence():
    """Test result persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=project_dir)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=project_dir)
        
        # Create canary and add result
        canary1 = CanarySession(project_dir)
        canary1.results.append(CanaryResult(
            canary_id="persist-test",
            timestamp="2026-02-13T12:00:00",
            control_output="OK",
            canary_output="OK",
            control_duration=1.0,
            canary_duration=1.0,
            diff_score=0.0,
            passed=True,
            regression_detected=False
        ))
        canary1._save_results()
        
        # Create new instance (simulating restart)
        canary2 = CanarySession(project_dir)
        
        # Should load persisted results
        assert len(canary2.results) == 1
        assert canary2.results[0].canary_id == "persist-test"


if __name__ == '__main__':
    test_canary_result()
    test_diff_score_calculation()
    test_regression_detection()
    test_canary_stats()
    test_persistence()
    print("✅ All canary session tests passed!")
