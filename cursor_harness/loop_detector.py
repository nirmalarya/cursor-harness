"""
Loop detector for cursor-harness v3.0.

Detects when agent is stuck reading files repeatedly.
Simple, effective pattern.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple


class LoopDetector:
    """Detect when agent is stuck in a loop."""
    
    def __init__(self, max_repeated_reads: int = 12, session_timeout_minutes: int = 60):
        self.max_repeated_reads = max_repeated_reads
        self.session_timeout = session_timeout_minutes * 60
        
        self.session_start = time.time()
        self.file_reads = defaultdict(int)
        self.tool_count = 0
        self.last_progress = time.time()
    
    def track_tool(self, tool_type: str, path: str = ""):
        """Track a tool call."""
        self.tool_count += 1
        self.last_progress = time.time()
        
        if tool_type == "read" and path:
            self.file_reads[path] += 1
    
    def check(self) -> Tuple[bool, str]:
        """
        Check if agent is stuck in a loop.
        
        Returns:
            (is_stuck, reason)
        """
        
        # Check 1: Timeout
        elapsed = time.time() - self.session_start
        if elapsed > self.session_timeout:
            return True, f"Session timeout ({elapsed/60:.0f} minutes)"
        
        # Check 2: Repeated file reads
        for path, count in self.file_reads.items():
            if count > self.max_repeated_reads:
                return True, f"Reading {path} {count} times"
        
        # Check 3: No progress (only reading, no writing)
        if self.tool_count > 30:
            # Count non-read tools
            non_reads = self.tool_count - sum(self.file_reads.values())
            if non_reads == 0:
                return True, f"{self.tool_count} reads, 0 writes/edits"
        
        return False, ""
    
    def reset(self):
        """Reset for new session."""
        self.session_start = time.time()
        self.file_reads.clear()
        self.tool_count = 0
        self.last_progress = time.time()

