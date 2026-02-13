"""Tests for performance profiler."""

import tempfile
from pathlib import Path
import time

from cursor_harness.intelligence.performance_profiler import PerformanceProfiler, ProfileMetric, SessionProfile


def test_profile_metric():
    """Test profile metric creation and completion."""
    metric = ProfileMetric(
        name="test_operation",
        start_time=time.time(),
        metadata={'key': 'value'}
    )
    
    time.sleep(0.01)
    metric.complete()
    
    assert metric.end_time is not None
    assert metric.duration is not None
    assert metric.duration > 0


def test_measure_context_manager():
    """Test measure context manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profiler = PerformanceProfiler(Path(tmpdir), "test-session")
        
        with profiler.measure("test_op", param="value"):
            time.sleep(0.01)
        
        assert len(profiler.profile.metrics) == 1
        assert profiler.profile.metrics[0].name == "test_op"
        assert profiler.profile.metrics[0].duration > 0
        assert profiler.profile.metrics[0].metadata['param'] == "value"


def test_start_stop_metric():
    """Test start/stop metric API."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profiler = PerformanceProfiler(Path(tmpdir), "test-session")
        
        key = profiler.start_metric("operation", tag="test")
        time.sleep(0.01)
        profiler.stop_metric(key)
        
        assert len(profiler.profile.metrics) == 1
        assert profiler.profile.metrics[0].duration > 0


def test_record_point():
    """Test recording point-in-time metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profiler = PerformanceProfiler(Path(tmpdir), "test-session")
        
        profiler.record_point("token_count", 1500, model="gpt-4")
        
        assert len(profiler.profile.metrics) == 1
        assert profiler.profile.metrics[0].name == "token_count"
        assert profiler.profile.metrics[0].duration == 1500


def test_session_summary():
    """Test session summary computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profiler = PerformanceProfiler(Path(tmpdir), "test-session")
        
        # Record various operations
        with profiler.measure("llm_call"):
            time.sleep(0.01)
        
        with profiler.measure("llm_call"):
            time.sleep(0.01)
        
        with profiler.measure("file_write"):
            time.sleep(0.005)
        
        profiler.complete_session()
        summary = profiler.get_summary()
        
        assert summary['total_metrics'] == 3
        assert 'llm_call' in summary['by_operation']
        assert summary['by_operation']['llm_call']['count'] == 2
        assert 'file_write' in summary['by_operation']


def test_slowest_operations():
    """Test getting slowest operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profiler = PerformanceProfiler(Path(tmpdir), "test-session")
        
        # Record operations with different durations
        with profiler.measure("fast"):
            time.sleep(0.001)
        
        with profiler.measure("slow"):
            time.sleep(0.05)
        
        with profiler.measure("medium"):
            time.sleep(0.01)
        
        slowest = profiler.get_slowest_operations(limit=2)
        
        assert len(slowest) <= 2
        assert slowest[0].name == "slow"  # Slowest first


def test_operation_stats():
    """Test getting stats for specific operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profiler = PerformanceProfiler(Path(tmpdir), "test-session")
        
        # Record multiple instances of same operation
        for i in range(3):
            with profiler.measure("test_op"):
                time.sleep(0.01)
        
        profiler.complete_session()
        stats = profiler.get_operation_stats("test_op")
        
        assert stats is not None
        assert stats['count'] == 3
        assert 'avg' in stats
        assert 'min' in stats
        assert 'max' in stats


def test_persistence():
    """Test saving and loading profiles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        session_id = "persist-test"
        
        # Create and save profile
        profiler1 = PerformanceProfiler(project_dir, session_id)
        with profiler1.measure("operation"):
            time.sleep(0.01)
        profiler1.complete_session()
        
        # Load profile
        profiler2 = PerformanceProfiler.load_session(project_dir, session_id)
        
        assert profiler2 is not None
        assert len(profiler2.profile.metrics) == 1
        assert profiler2.profile.session_id == session_id


def test_get_all_sessions():
    """Test getting list of all sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create multiple sessions
        for i in range(3):
            profiler = PerformanceProfiler(project_dir, f"session-{i}")
            with profiler.measure("op"):
                pass
            profiler.save()
        
        sessions = PerformanceProfiler.get_all_sessions(project_dir)
        
        assert len(sessions) == 3
        assert "session-0" in sessions


def test_compare_sessions():
    """Test session comparison."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create first session
        prof1 = PerformanceProfiler(project_dir, "session1")
        with prof1.measure("llm_call"):
            time.sleep(0.01)
        prof1.complete_session()
        
        # Create second session (slower)
        prof2 = PerformanceProfiler(project_dir, "session2")
        with prof2.measure("llm_call"):
            time.sleep(0.02)
        prof2.complete_session()
        
        # Compare
        comparison = PerformanceProfiler.compare_sessions(
            project_dir,
            "session1",
            "session2"
        )
        
        assert 'session1' in comparison
        assert 'session2' in comparison
        assert 'differences' in comparison
        assert 'llm_call' in comparison['differences']


if __name__ == '__main__':
    test_profile_metric()
    test_measure_context_manager()
    test_start_stop_metric()
    test_record_point()
    test_session_summary()
    test_slowest_operations()
    test_operation_stats()
    test_persistence()
    test_get_all_sessions()
    test_compare_sessions()
    print("✅ All performance profiler tests passed!")
