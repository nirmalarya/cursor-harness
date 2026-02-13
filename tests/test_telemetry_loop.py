"""Tests for telemetry and action loop."""

import tempfile
from pathlib import Path
import time

from cursor_harness.intelligence.telemetry_loop import TelemetryLoop, TelemetryEvent, ActionTrigger


def test_telemetry_event():
    """Test telemetry event creation."""
    event = TelemetryEvent(
        event_type="error",
        timestamp=time.time(),
        session_id="sess123",
        iteration=5,
        data={'message': 'Test error', 'severity': 'high'}
    )
    
    assert event.event_type == "error"
    assert event.session_id == "sess123"
    assert event.data['message'] == 'Test error'
    
    # Test serialization
    data = event.to_dict()
    restored = TelemetryEvent.from_dict(data)
    assert restored.event_type == event.event_type
    assert restored.data == event.data


def test_record_event():
    """Test recording events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loop = TelemetryLoop(Path(tmpdir))
        
        loop.record(
            event_type="verification",
            session_id="test",
            iteration=1,
            passed=True,
            duration=5.2
        )
        
        assert len(loop.events) == 1
        assert loop.events[0].event_type == "verification"
        assert loop.events[0].data['passed'] is True


def test_high_error_rate_trigger():
    """Test high error rate triggers action."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loop = TelemetryLoop(Path(tmpdir))
        
        # Record many errors
        for i in range(15):
            loop.record(
                event_type="error",
                session_id="test",
                iteration=i,
                message=f"Error {i}"
            )
        
        # Should have triggered reduce_complexity action
        complexity_triggers = [
            t for t in loop.triggers
            if t.condition == "high_error_rate"
        ]
        
        assert len(complexity_triggers) > 0
        assert complexity_triggers[0].action_type == "reduce_complexity"


def test_consecutive_verification_failures():
    """Test consecutive verification failures trigger rollback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loop = TelemetryLoop(Path(tmpdir))
        
        # Record 3 consecutive failures
        for i in range(3):
            loop.record(
                event_type="verification",
                session_id="test",
                iteration=i,
                passed=False
            )
        
        # Should trigger rollback
        rollback_triggers = [
            t for t in loop.triggers
            if t.condition == "consecutive_verification_failures"
        ]
        
        assert len(rollback_triggers) > 0
        assert rollback_triggers[0].action_type == "rollback_checkpoint"


def test_slow_iterations_trigger():
    """Test slow iterations trigger optimization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loop = TelemetryLoop(Path(tmpdir))
        
        # Record slow iterations
        for i in range(6):
            loop.record(
                event_type="performance",
                session_id="test",
                iteration=i,
                duration=350.0  # >5 minutes
            )
        
        # Should trigger optimize_prompts
        optimize_triggers = [
            t for t in loop.triggers
            if t.condition == "slow_iterations"
        ]
        
        assert len(optimize_triggers) > 0
        assert optimize_triggers[0].action_type == "optimize_prompts"


def test_action_handler_registration():
    """Test custom action handler registration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loop = TelemetryLoop(Path(tmpdir))
        
        executed = []
        
        def custom_handler(params):
            executed.append(params)
        
        loop.register_action_handler('custom_action', custom_handler)
        
        # Manually trigger action
        loop._trigger_action(
            condition="test_condition",
            action_type="custom_action",
            action_params={'test': 'data'}
        )
        
        # Handler should have been called
        assert len(executed) == 1
        assert executed[0]['test'] == 'data'


def test_stats():
    """Test telemetry statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loop = TelemetryLoop(Path(tmpdir))
        
        # Record various events
        loop.record("error", "test", 1, message="Error 1")
        loop.record("error", "test", 2, message="Error 2")
        loop.record("verification", "test", 3, passed=True)
        loop.record("performance", "test", 4, duration=10.0)
        
        stats = loop.get_stats()
        
        assert stats['total_events'] == 4
        assert stats['by_type']['error'] == 2
        assert stats['by_type']['verification'] == 1
        assert stats['by_type']['performance'] == 1


def test_get_recent_events():
    """Test filtering recent events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loop = TelemetryLoop(Path(tmpdir))
        
        # Record mixed events
        for i in range(10):
            loop.record("error", "test", i, message=f"Error {i}")
            loop.record("verification", "test", i, passed=True)
        
        # Get all recent
        all_recent = loop.get_recent_events(limit=5)
        assert len(all_recent) == 5
        
        # Get only errors
        error_recent = loop.get_recent_events(event_type="error", limit=5)
        assert len(error_recent) == 5
        assert all(e.event_type == "error" for e in error_recent)


def test_trigger_persistence():
    """Test trigger persistence across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create loop and trigger action
        loop1 = TelemetryLoop(project_dir)
        loop1._trigger_action(
            condition="test_persist",
            action_type="reduce_complexity",
            action_params={'reason': 'persistence test'}
        )
        
        # Create new instance (simulating restart)
        loop2 = TelemetryLoop(project_dir)
        
        # Should load persisted triggers
        assert len(loop2.triggers) == 1
        assert loop2.triggers[0].condition == "test_persist"


if __name__ == '__main__':
    test_telemetry_event()
    test_record_event()
    test_high_error_rate_trigger()
    test_consecutive_verification_failures()
    test_slow_iterations_trigger()
    test_action_handler_registration()
    test_stats()
    test_get_recent_events()
    test_trigger_persistence()
    print("✅ All telemetry loop tests passed!")
