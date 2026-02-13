"""Tests for session analytics."""

import json
import tempfile
from pathlib import Path

from cursor_harness.intelligence.session_analytics import SessionAnalytics, AnalyticsSummary


def test_analytics_summary_creation():
    """Test analytics summary dataclass."""
    summary = AnalyticsSummary(
        total_sessions=10,
        total_duration=1000.0,
        avg_duration=100.0,
        success_rate=0.9,
        total_errors=5,
        total_recoveries=3,
        top_operations=[],
        trends={}
    )
    
    assert summary.total_sessions == 10
    assert summary.success_rate == 0.9
    
    # Test serialization
    data = summary.to_dict()
    assert data['total_sessions'] == 10


def test_empty_project_summary():
    """Test summary with no data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = SessionAnalytics(Path(tmpdir))
        
        summary = analytics.get_summary()
        
        assert summary.total_sessions == 0
        assert summary.total_duration == 0.0
        assert summary.avg_duration == 0.0


def test_summary_with_profiles():
    """Test summary with mock profile data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create profiling directory and mock profiles
        profiling_dir = project_dir / ".cursor" / "profiling"
        profiling_dir.mkdir(parents=True)
        
        # Create mock profile
        profile = {
            'session_id': 'test-session',
            'start_time': 1000.0,
            'end_time': 1100.0,
            'total_duration': 100.0,
            'summary': {
                'total_metrics': 5,
                'by_operation': {
                    'llm_call': {
                        'count': 3,
                        'total': 50.0,
                        'avg': 16.67,
                        'min': 15.0,
                        'max': 18.0
                    }
                }
            }
        }
        
        with open(profiling_dir / "test-session.json", 'w') as f:
            json.dump(profile, f)
        
        analytics = SessionAnalytics(project_dir)
        summary = analytics.get_summary()
        
        assert summary.total_sessions == 1
        assert summary.total_duration == 100.0
        assert summary.avg_duration == 100.0


def test_top_operations():
    """Test getting top operations across sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        profiling_dir = project_dir / ".cursor" / "profiling"
        profiling_dir.mkdir(parents=True)
        
        # Create multiple profiles with different operations
        for i in range(3):
            profile = {
                'session_id': f'session-{i}',
                'total_duration': 100.0,
                'summary': {
                    'by_operation': {
                        'llm_call': {'count': 2, 'total': 30.0},
                        'file_write': {'count': 1, 'total': 5.0}
                    }
                }
            }
            with open(profiling_dir / f"session-{i}.json", 'w') as f:
                json.dump(profile, f)
        
        analytics = SessionAnalytics(project_dir)
        summary = analytics.get_summary()
        
        # llm_call should be top (90.0 total across 3 sessions)
        assert len(summary.top_operations) > 0
        assert summary.top_operations[0]['operation'] == 'llm_call'


def test_operation_trends():
    """Test operation trends across sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        profiling_dir = project_dir / ".cursor" / "profiling"
        profiling_dir.mkdir(parents=True)
        
        # Create sessions with increasing duration for an operation
        for i in range(5):
            profile = {
                'session_id': f'session-{i}',
                'total_duration': 100.0,
                'summary': {
                    'by_operation': {
                        'llm_call': {
                            'count': 1,
                            'avg': 10.0 + i * 2.0  # Increasing trend
                        }
                    }
                }
            }
            with open(profiling_dir / f"session-{i}.json", 'w') as f:
                json.dump(profile, f)
        
        analytics = SessionAnalytics(project_dir)
        trends = analytics.get_operation_trends('llm_call')
        
        assert trends['operation'] == 'llm_call'
        assert len(trends['sessions']) == 5
        assert len(trends['avg_durations']) == 5
        assert trends['trend_direction'] in ['improving', 'declining', 'stable']


def test_error_analysis():
    """Test error analysis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        telemetry_dir = project_dir / ".cursor" / "telemetry"
        telemetry_dir.mkdir(parents=True)
        
        # Create mock telemetry events
        events = [
            {'event_type': 'error', 'session_id': 'sess1', 'data': {'type': 'timeout'}},
            {'event_type': 'error', 'session_id': 'sess1', 'data': {'type': 'timeout'}},
            {'event_type': 'error', 'session_id': 'sess2', 'data': {'type': 'validation'}},
            {'event_type': 'verification', 'session_id': 'sess1', 'data': {}}
        ]
        
        with open(telemetry_dir / "events.jsonl", 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')
        
        analytics = SessionAnalytics(project_dir)
        error_analysis = analytics.get_error_analysis()
        
        assert error_analysis['total_errors'] == 3
        assert error_analysis['by_type']['timeout'] == 2
        assert error_analysis['by_type']['validation'] == 1


def test_export_report():
    """Test exporting analytics report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        analytics = SessionAnalytics(project_dir)
        report_json = analytics.export_report()
        
        # Should be valid JSON
        report = json.loads(report_json)
        
        assert 'generated_at' in report
        assert 'summary' in report
        assert 'error_analysis' in report


def test_trend_direction_computation():
    """Test trend direction logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = SessionAnalytics(Path(tmpdir))
        
        # Improving trend
        improving = analytics._compute_trend_direction([100, 95, 90, 85, 80])
        assert improving == 'improving'
        
        # Declining trend
        declining = analytics._compute_trend_direction([80, 85, 90, 95, 100])
        assert declining == 'declining'
        
        # Stable trend
        stable = analytics._compute_trend_direction([100, 99, 101, 100, 100])
        assert stable == 'stable'


if __name__ == '__main__':
    test_analytics_summary_creation()
    test_empty_project_summary()
    test_summary_with_profiles()
    test_top_operations()
    test_operation_trends()
    test_error_analysis()
    test_export_report()
    test_trend_direction_computation()
    print("✅ All session analytics tests passed!")
