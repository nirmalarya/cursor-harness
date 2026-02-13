"""
Intelligence layer for cursor-harness v5.0.0.

Cross-session learning and adaptation:
- Error pattern learning
- Adaptive prompting
- Dependency graph
- Session profiling
"""

from .pattern_db import PatternDatabase, ErrorPattern
from .adaptive_prompter import AdaptivePrompter
from .dependency_graph import DependencyGraph, TaskNode

__all__ = ['PatternDatabase', 'ErrorPattern', 'AdaptivePrompter', 'DependencyGraph', 'TaskNode']
