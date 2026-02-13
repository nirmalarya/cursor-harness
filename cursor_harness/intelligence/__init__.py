"""
Intelligence layer for cursor-harness v5.0.0.

Cross-session learning and adaptation:
- Error pattern learning
- Adaptive prompting
- Dependency graph
- Canary sessions
- Session profiling
"""

from .pattern_db import PatternDatabase, ErrorPattern
from .adaptive_prompter import AdaptivePrompter
from .dependency_graph import DependencyGraph, TaskNode
from .canary_session import CanarySession, CanaryResult
from .telemetry_loop import TelemetryLoop, TelemetryEvent, ActionTrigger
from .auto_recovery import AutoRecovery, RecoveryStrategy, RecoveryAction

__all__ = ['PatternDatabase', 'ErrorPattern', 'AdaptivePrompter', 'DependencyGraph', 'TaskNode', 'CanarySession', 'CanaryResult', 'TelemetryLoop', 'TelemetryEvent', 'ActionTrigger', 'AutoRecovery', 'RecoveryStrategy', 'RecoveryAction']
