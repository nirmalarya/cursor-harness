"""
Verification pipeline for cursor-harness.

After each coding iteration, run automated checks:
- Git diff analysis (detect unintended changes, large deletions)
- Test execution
- Lint/format checks

On failures, trigger LLM self-correction before proceeding.
"""

from .git_analyzer import GitAnalyzer
from .verification_pipeline import VerificationPipeline, VerificationResult

__all__ = ['GitAnalyzer', 'VerificationPipeline', 'VerificationResult']
