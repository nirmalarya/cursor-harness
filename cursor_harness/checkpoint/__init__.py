"""
Git checkpoint system for cursor-harness.

Auto-commit at safe points during sessions. Rollback on failures.
"""

from .checkpoint_manager import CheckpointManager, Checkpoint

__all__ = ['CheckpointManager', 'Checkpoint']
