"""
Error pattern database for adaptive prompting.

Stores error patterns across sessions and tracks successful resolutions.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ErrorPattern:
    """A learned error pattern."""
    pattern_id: str  # Hash of error signature
    error_type: str  # e.g., "test_failure", "lint_error", "verification_failure"
    signature: str  # Normalized error message/pattern
    first_seen: str  # ISO timestamp
    last_seen: str  # ISO timestamp
    occurrence_count: int
    resolution_count: int  # How many times successfully resolved
    success_rate: float  # resolution_count / occurrence_count
    
    # Learning data
    successful_fixes: List[str]  # Descriptions of what worked
    failed_fixes: List[str]  # Descriptions of what didn't work
    
    # Context
    repo_path: str
    file_patterns: Set[str]  # Which files this error commonly affects
    
    # Decay
    relevance_score: float  # Decays over time if not seen recently
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        d = asdict(self)
        d['file_patterns'] = list(self.file_patterns)  # Convert set to list
        return d
    
    @staticmethod
    def from_dict(data: Dict) -> 'ErrorPattern':
        """Create from dictionary."""
        data['file_patterns'] = set(data.get('file_patterns', []))
        return ErrorPattern(**data)
    
    def to_prompt_text(self) -> str:
        """Convert to text for injection into system prompt."""
        lines = [
            f"**Known Issue ({self.error_type}):**",
            f"{self.signature}",
            ""
        ]
        
        if self.successful_fixes:
            lines.append("**What worked:**")
            for fix in self.successful_fixes[-3:]:  # Last 3 successful fixes
                lines.append(f"- {fix}")
            lines.append("")
        
        if self.failed_fixes:
            lines.append("**What didn't work:**")
            for fix in self.failed_fixes[-2:]:  # Last 2 failed attempts
                lines.append(f"- {fix}")
            lines.append("")
        
        if self.file_patterns:
            lines.append(f"**Common files:** {', '.join(list(self.file_patterns)[:5])}")
            lines.append("")
        
        return '\n'.join(lines)


class PatternDatabase:
    """
    Database of error patterns learned across sessions.
    
    Stores patterns in JSON file in project's .cursor directory.
    """
    
    def __init__(self, project_dir: Path, decay_rate: float = 0.9):
        """
        Initialize pattern database.
        
        Args:
            project_dir: Project directory
            decay_rate: Relevance decay per day (0.9 = 10% decay per day)
        """
        self.project_dir = Path(project_dir)
        self.decay_rate = decay_rate
        
        self.db_dir = self.project_dir / ".cursor" / "intelligence"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.db_dir / "patterns.json"
        
        self.patterns: Dict[str, ErrorPattern] = {}
        self._load()
    
    def _load(self):
        """Load patterns from disk."""
        if not self.db_file.exists():
            return
        
        try:
            with open(self.db_file, 'r') as f:
                data = json.load(f)
                self.patterns = {
                    pid: ErrorPattern.from_dict(pdata)
                    for pid, pdata in data.items()
                }
        except Exception as e:
            print(f"   ⚠️  Failed to load pattern database: {e}")
    
    def _save(self):
        """Save patterns to disk."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(
                    {pid: p.to_dict() for pid, p in self.patterns.items()},
                    f,
                    indent=2
                )
        except Exception as e:
            print(f"   ⚠️  Failed to save pattern database: {e}")
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        files_affected: Optional[List[str]] = None
    ) -> str:
        """
        Record an error occurrence.
        
        Returns:
            pattern_id for tracking this error
        """
        # Normalize error message (remove timestamps, line numbers, etc.)
        signature = self._normalize_error(error_message)
        pattern_id = self._hash_signature(signature)
        
        now = datetime.utcnow().isoformat()
        
        if pattern_id in self.patterns:
            # Update existing pattern
            pattern = self.patterns[pattern_id]
            pattern.occurrence_count += 1
            pattern.last_seen = now
            
            if files_affected:
                pattern.file_patterns.update(files_affected)
        else:
            # Create new pattern
            pattern = ErrorPattern(
                pattern_id=pattern_id,
                error_type=error_type,
                signature=signature,
                first_seen=now,
                last_seen=now,
                occurrence_count=1,
                resolution_count=0,
                success_rate=0.0,
                successful_fixes=[],
                failed_fixes=[],
                repo_path=str(self.project_dir),
                file_patterns=set(files_affected or []),
                relevance_score=1.0
            )
            self.patterns[pattern_id] = pattern
        
        self._save()
        return pattern_id
    
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
            fix_description: What was done
        """
        if pattern_id not in self.patterns:
            return
        
        pattern = self.patterns[pattern_id]
        
        if success:
            pattern.resolution_count += 1
            pattern.successful_fixes.append(fix_description)
            # Boost relevance on successful resolution
            pattern.relevance_score = min(1.0, pattern.relevance_score + 0.1)
        else:
            pattern.failed_fixes.append(fix_description)
        
        # Update success rate
        if pattern.occurrence_count > 0:
            pattern.success_rate = pattern.resolution_count / pattern.occurrence_count
        
        self._save()
    
    def get_relevant_patterns(
        self,
        max_patterns: int = 5,
        min_relevance: float = 0.3,
        error_types: Optional[List[str]] = None
    ) -> List[ErrorPattern]:
        """
        Get most relevant patterns for current session.
        
        Args:
            max_patterns: Maximum number of patterns to return
            min_relevance: Minimum relevance score
            error_types: Filter by error types
        
        Returns:
            List of relevant patterns, sorted by relevance
        """
        # Apply relevance decay based on last seen
        self._apply_decay()
        
        # Filter and sort
        candidates = []
        for pattern in self.patterns.values():
            if pattern.relevance_score < min_relevance:
                continue
            
            if error_types and pattern.error_type not in error_types:
                continue
            
            # Prefer patterns with successful resolutions
            score = pattern.relevance_score * (1 + pattern.success_rate)
            candidates.append((score, pattern))
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        return [p for _, p in candidates[:max_patterns]]
    
    def _apply_decay(self):
        """Apply time-based relevance decay."""
        now = datetime.utcnow()
        
        for pattern in self.patterns.values():
            try:
                last_seen = datetime.fromisoformat(pattern.last_seen)
                days_ago = (now - last_seen).days
                
                # Decay exponentially: score * (decay_rate ^ days)
                decay_factor = self.decay_rate ** days_ago
                pattern.relevance_score *= decay_factor
            except:
                pass
    
    def _normalize_error(self, error_message: str) -> str:
        """
        Normalize error message to create stable signature.
        
        Removes:
        - Timestamps
        - Line numbers
        - File paths (keeps just filename)
        - Hex addresses
        """
        import re
        
        # Remove timestamps
        msg = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '', error_message)
        msg = re.sub(r'\d{2}:\d{2}:\d{2}', '', msg)
        
        # Remove line numbers (line 123, :45, etc.)
        msg = re.sub(r'line \d+', 'line X', msg, flags=re.IGNORECASE)
        msg = re.sub(r':\d+:', ':X:', msg)
        
        # Remove hex addresses
        msg = re.sub(r'0x[0-9a-fA-F]+', '0xXXX', msg)
        
        # Normalize file paths (keep just filename)
        msg = re.sub(r'[/\\][\w/\\.-]+\.(\w+)', 'file.\\1', msg)
        
        # Normalize whitespace
        msg = ' '.join(msg.split())
        
        return msg.strip()
    
    def _hash_signature(self, signature: str) -> str:
        """Generate stable hash for error signature."""
        return hashlib.md5(signature.encode()).hexdigest()[:12]
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        total = len(self.patterns)
        resolved = sum(1 for p in self.patterns.values() if p.resolution_count > 0)
        avg_success = sum(p.success_rate for p in self.patterns.values()) / total if total > 0 else 0
        
        return {
            'total_patterns': total,
            'resolved_patterns': resolved,
            'avg_success_rate': avg_success,
            'db_file': str(self.db_file)
        }
