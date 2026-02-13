"""Tests for auto-recovery system."""

import tempfile
from pathlib import Path
import time

from cursor_harness.intelligence.auto_recovery import AutoRecovery, RecoveryStrategy, RecoveryAction


def test_recovery_action():
    """Test recovery action creation."""
    action = RecoveryAction(
        action_id="test123",
        timestamp="2026-02-13T18:00:00",
        failure_type="verification_failure",
        strategy="checkpoint_rollback",
        parameters={'consecutive_failures': 3},
        success=True,
        notes="Rollback successful"
    )
    
    assert action.action_id == "test123"
    assert action.failure_type == "verification_failure"
    assert action.success is True
    
    # Test serialization
    data = action.to_dict()
    restored = RecoveryAction.from_dict(data)
    assert restored.action_id == action.action_id
    assert restored.strategy == action.strategy


def test_strategy_selection_verification_failure():
    """Test strategy selection for verification failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        # First failure: retry
        recovery.state['consecutive_failures'] = 0
        strategy = recovery._select_strategy("verification_failure", {})
        assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
        
        # Second failure: still retry
        recovery.state['consecutive_failures'] = 1
        strategy = recovery._select_strategy("verification_failure", {})
        assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
        
        # Third failure: simplify
        recovery.state['consecutive_failures'] = 2
        strategy = recovery._select_strategy("verification_failure", {})
        assert strategy == RecoveryStrategy.SIMPLIFY_TASK
        
        # Fourth failure: rollback
        recovery.state['consecutive_failures'] = 3
        strategy = recovery._select_strategy("verification_failure", {})
        assert strategy == RecoveryStrategy.CHECKPOINT_ROLLBACK


def test_strategy_selection_timeout():
    """Test strategy selection for timeouts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        # First timeout: retry
        recovery.state['retry_count'] = 0
        strategy = recovery._select_strategy("timeout", {})
        assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
        
        # After retries: reduce scope
        recovery.state['retry_count'] = 2
        strategy = recovery._select_strategy("timeout", {})
        assert strategy == RecoveryStrategy.REDUCE_SCOPE


def test_strategy_selection_loop():
    """Test strategy selection for loop detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        strategy = recovery._select_strategy("loop_detected", {})
        assert strategy == RecoveryStrategy.BREAK_INTO_SUBTASKS


def test_strategy_selection_context_overflow():
    """Test strategy selection for context overflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        strategy = recovery._select_strategy("context_overflow", {})
        assert strategy == RecoveryStrategy.REDUCE_CONTEXT


def test_detect_and_recover():
    """Test full detect and recover cycle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        # Trigger recovery
        action = recovery.detect_and_recover(
            failure_type="verification_failure",
            context={'error': 'Tests failed'}
        )
        
        assert action is not None
        assert action.failure_type == "verification_failure"
        assert action.strategy in [s.value for s in RecoveryStrategy]
        
        # If successful, consecutive_failures should be reset
        # If failed, should be incremented
        if action.success:
            assert recovery.state['consecutive_failures'] == 0
        else:
            assert recovery.state['consecutive_failures'] >= 1


def test_custom_strategy_handler():
    """Test custom strategy handler registration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        executed = []
        
        def custom_handler(context):
            executed.append(context)
            return {'success': True, 'notes': 'Custom recovery'}
        
        recovery.register_strategy_handler(
            RecoveryStrategy.SKIP_AND_CONTINUE,
            custom_handler
        )
        
        # Trigger recovery that uses this strategy
        action = recovery.detect_and_recover(
            failure_type="dependency_failure",
            context={'critical': False, 'dep': 'test_dep'}
        )
        
        # Handler should have been called
        assert len(executed) == 1
        assert executed[0]['dep'] == 'test_dep'
        assert action.success is True


def test_mark_success():
    """Test marking recovery as successful."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        # Set failure state
        recovery.state['consecutive_failures'] = 3
        recovery.state['retry_count'] = 2
        
        # Mark success
        recovery.mark_success()
        
        # State should reset
        assert recovery.state['consecutive_failures'] == 0
        assert recovery.state['retry_count'] == 0
        assert recovery.state['last_success_time'] is not None


def test_stats():
    """Test recovery statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        # Trigger various recoveries
        recovery.detect_and_recover("verification_failure", {})
        recovery.detect_and_recover("timeout", {})
        recovery.detect_and_recover("loop_detected", {})
        
        stats = recovery.get_stats()
        
        assert stats['total_recoveries'] == 3
        assert 'by_strategy' in stats
        assert 'by_failure_type' in stats
        assert stats['by_failure_type']['verification_failure'] == 1
        assert stats['by_failure_type']['timeout'] == 1


def test_persistence():
    """Test action and state persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create recovery and trigger action
        recovery1 = AutoRecovery(project_dir)
        recovery1.detect_and_recover("verification_failure", {'test': 'data'})
        recovery1.state['consecutive_failures'] = 5
        recovery1._save_state()
        
        # Create new instance (simulating restart)
        recovery2 = AutoRecovery(project_dir)
        
        # Should load persisted actions and state
        assert len(recovery2.actions) == 1
        assert recovery2.actions[0].failure_type == "verification_failure"
        assert recovery2.state['consecutive_failures'] == 5


def test_escalating_strategies():
    """Test that strategies escalate with consecutive failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recovery = AutoRecovery(Path(tmpdir))
        
        strategies = []
        
        # Simulate consecutive verification failures by manually incrementing
        # (normally failures would increment, but our test handlers succeed)
        for i in range(4):
            recovery.state['consecutive_failures'] = i
            strategy = recovery._select_strategy("verification_failure", {})
            if strategy:
                strategies.append(strategy.value)
        
        # Should see escalation: retry → simplify → rollback
        assert RecoveryStrategy.RETRY_WITH_BACKOFF.value in strategies
        assert RecoveryStrategy.SIMPLIFY_TASK.value in strategies
        assert RecoveryStrategy.CHECKPOINT_ROLLBACK.value in strategies


if __name__ == '__main__':
    test_recovery_action()
    test_strategy_selection_verification_failure()
    test_strategy_selection_timeout()
    test_strategy_selection_loop()
    test_strategy_selection_context_overflow()
    test_detect_and_recover()
    test_custom_strategy_handler()
    test_mark_success()
    test_stats()
    test_persistence()
    test_escalating_strategies()
    print("✅ All auto-recovery tests passed!")
