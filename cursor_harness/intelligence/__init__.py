"""
Intelligence layer for cursor-harness v5.0.0.

Cross-session learning and adaptation:
- Error pattern learning
- Adaptive prompting
- Session profiling
"""

from .pattern_db import PatternDatabase, ErrorPattern
from .adaptive_prompter import AdaptivePrompter

__all__ = ['PatternDatabase', 'ErrorPattern', 'AdaptivePrompter']
