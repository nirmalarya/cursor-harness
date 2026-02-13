"""Tests for Git checkpoint manager."""

import subprocess
import tempfile
from pathlib import Path

from cursor_harness.checkpoint.checkpoint_manager import CheckpointManager, Checkpoint


def test_checkpoint_creation():
    """Test creating checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create checkpoint manager (auto-inits git)
        manager = CheckpointManager(project_dir, session_id="test-session")
        
        # Create a file
        (project_dir / "test.txt").write_text("Hello world")
        
        # Create checkpoint
        checkpoint = manager.create_checkpoint(
            iteration=1,
            verification_passed=True,
            message="Test checkpoint"
        )
        
        assert checkpoint is not None
        assert checkpoint.session_id == "test-session"
        assert checkpoint.iteration == 1
        assert checkpoint.verification_passed is True
        assert len(checkpoint.files_changed) > 0
        
        # Verify git commit exists
        result = subprocess.run(
            ['git', 'log', '--oneline', '-1'],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        assert "Test checkpoint" in result.stdout


def test_rollback_to_checkpoint():
    """Test rolling back to a checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        manager = CheckpointManager(project_dir, session_id="test-session")
        
        # Create initial file and checkpoint
        (project_dir / "test.txt").write_text("Version 1")
        cp1 = manager.create_checkpoint(
            iteration=1,
            verification_passed=True
        )
        assert cp1 is not None
        
        # Modify file and create second checkpoint
        (project_dir / "test.txt").write_text("Version 2")
        cp2 = manager.create_checkpoint(
            iteration=2,
            verification_passed=True
        )
        assert cp2 is not None
        
        # Rollback to first checkpoint (soft)
        success = manager.rollback_to_checkpoint(cp1, hard=False)
        assert success is True
        
        # Verify we're at cp1 commit
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == cp1.commit_hash


def test_last_good_checkpoint():
    """Test finding last checkpoint with passing verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        manager = CheckpointManager(project_dir, session_id="test-session")
        
        # Create passing checkpoint
        (project_dir / "test1.txt").write_text("Test 1")
        cp1 = manager.create_checkpoint(
            iteration=1,
            verification_passed=True
        )
        
        # Create failing checkpoint
        (project_dir / "test2.txt").write_text("Test 2")
        cp2 = manager.create_checkpoint(
            iteration=2,
            verification_passed=False
        )
        
        # Get last good checkpoint
        last_good = manager.get_last_good_checkpoint()
        
        assert last_good is not None
        assert last_good.commit_hash == cp1.commit_hash
        assert last_good.verification_passed is True


def test_auto_rollback():
    """Test automatic rollback on consecutive failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        manager = CheckpointManager(project_dir, session_id="test-session")
        
        # Create good checkpoint
        (project_dir / "good.txt").write_text("Good version")
        cp_good = manager.create_checkpoint(
            iteration=1,
            verification_passed=True
        )
        
        # Create failing checkpoints
        for i in range(3):
            (project_dir / f"bad{i}.txt").write_text(f"Bad version {i}")
            manager.create_checkpoint(
                iteration=i + 2,
                verification_passed=False
            )
        
        # Trigger auto-rollback (threshold=3)
        rollback_triggered = manager.auto_rollback_on_failure(
            consecutive_failures=3,
            threshold=3
        )
        
        assert rollback_triggered is True
        
        # Verify we're back at good checkpoint
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == cp_good.commit_hash


def test_checkpoint_persistence():
    """Test that checkpoints persist across manager instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        session_id = "persist-test"
        
        # Create checkpoint with first manager
        manager1 = CheckpointManager(project_dir, session_id=session_id)
        (project_dir / "test.txt").write_text("Test")
        cp1 = manager1.create_checkpoint(
            iteration=1,
            verification_passed=True
        )
        
        # Create new manager (simulating new session)
        manager2 = CheckpointManager(project_dir, session_id=session_id)
        
        # Should load persisted checkpoints
        assert len(manager2.checkpoints) == 1
        assert manager2.checkpoints[0].commit_hash == cp1.commit_hash


if __name__ == '__main__':
    test_checkpoint_creation()
    test_rollback_to_checkpoint()
    test_last_good_checkpoint()
    test_auto_rollback()
    test_checkpoint_persistence()
    print("✅ All checkpoint tests passed!")
