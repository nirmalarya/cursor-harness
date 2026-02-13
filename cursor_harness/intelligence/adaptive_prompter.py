"""
Adaptive prompter - injects learned patterns into system prompts.

Uses pattern database to augment prompts with relevant failure patterns
and successful resolutions from previous sessions.
"""

from pathlib import Path
from typing import Optional, List

from .pattern_db import PatternDatabase, ErrorPattern


class AdaptivePrompter:
    """
    Manages adaptive prompting based on learned patterns.
    
    Injects relevant error patterns into system prompts to help
    the LLM avoid known issues and apply proven solutions.
    """
    
    def __init__(
        self,
        project_dir: Path,
        enabled: bool = True,
        max_patterns: int = 5,
        min_relevance: float = 0.3
    ):
        """
        Initialize adaptive prompter.
        
        Args:
            project_dir: Project directory
            enabled: Whether adaptive prompting is enabled
            max_patterns: Maximum patterns to inject per prompt
            min_relevance: Minimum relevance score for injection
        """
        self.project_dir = Path(project_dir)
        self.enabled = enabled
        self.max_patterns = max_patterns
        self.min_relevance = min_relevance
        
        self.pattern_db = PatternDatabase(project_dir) if enabled else None
    
    def augment_prompt(
        self,
        base_prompt: str,
        error_types: Optional[List[str]] = None
    ) -> str:
        """
        Augment prompt with relevant learned patterns.
        
        Args:
            base_prompt: Original system prompt
            error_types: Filter patterns by type (None = all types)
        
        Returns:
            Augmented prompt with pattern injection
        """
        if not self.enabled or not self.pattern_db:
            return base_prompt
        
        # Get relevant patterns
        patterns = self.pattern_db.get_relevant_patterns(
            max_patterns=self.max_patterns,
            min_relevance=self.min_relevance,
            error_types=error_types
        )
        
        if not patterns:
            return base_prompt
        
        # Build pattern injection
        injection = self._build_pattern_injection(patterns)
        
        # Insert after system instructions but before task details
        # Look for common markers
        markers = [
            "\n## Your Task",
            "\n## Project Specification",
            "\n## Current Work Item",
            "\n---\n\n##"
        ]
        
        for marker in markers:
            if marker in base_prompt:
                parts = base_prompt.split(marker, 1)
                return f"{parts[0]}\n\n{injection}\n\n{marker}{parts[1]}"
        
        # Fallback: append at end
        return f"{base_prompt}\n\n{injection}"
    
    def _build_pattern_injection(self, patterns: List[ErrorPattern]) -> str:
        """Build the injection text from patterns."""
        lines = [
            "---",
            "",
            "## 🧠 Learned Patterns (Intelligence Layer)",
            "",
            "The following patterns were learned from previous sessions on this project.",
            "Please review and apply these learnings to avoid repeating mistakes:",
            ""
        ]
        
        for i, pattern in enumerate(patterns, 1):
            lines.append(f"### Pattern {i}: {pattern.error_type}")
            lines.append("")
            lines.append(pattern.to_prompt_text())
            
            # Show success rate if pattern has been resolved
            if pattern.resolution_count > 0:
                success_pct = pattern.success_rate * 100
                lines.append(f"**Success rate:** {success_pct:.0f}% ({pattern.resolution_count}/{pattern.occurrence_count} resolutions)")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        lines.append("Apply these learnings proactively to avoid known issues.")
        lines.append("")
        
        return '\n'.join(lines)
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        files_affected: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Record an error for learning.
        
        Args:
            error_type: Type of error (test_failure, lint_error, etc.)
            error_message: Error message or description
            files_affected: Files involved in the error
        
        Returns:
            pattern_id for tracking
        """
        if not self.enabled or not self.pattern_db:
            return None
        
        return self.pattern_db.record_error(
            error_type=error_type,
            error_message=error_message,
            files_affected=files_affected
        )
    
    def record_resolution(
        self,
        pattern_id: str,
        success: bool,
        fix_description: str
    ):
        """
        Record an attempted resolution.
        
        Args:
            pattern_id: Pattern ID from record_error
            success: Whether the fix worked
            fix_description: What was done to fix it
        """
        if not self.enabled or not self.pattern_db:
            return
        
        self.pattern_db.record_resolution(
            pattern_id=pattern_id,
            success=success,
            fix_description=fix_description
        )
    
    def get_stats(self) -> dict:
        """Get learning statistics."""
        if not self.enabled or not self.pattern_db:
            return {
                'enabled': False,
                'total_patterns': 0
            }
        
        stats = self.pattern_db.get_stats()
        stats['enabled'] = True
        stats['max_patterns'] = self.max_patterns
        stats['min_relevance'] = self.min_relevance
        
        return stats
