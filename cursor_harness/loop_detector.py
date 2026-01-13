"""
Loop Detector
=============

Detects when cursor-agent is stuck in infinite loops.
Works across ALL modes: greenfield, enhancement, bugfix, backlog.

Reliable detection without false positives!
"""

import time
from collections import deque
from pathlib import Path
from typing import List, Optional
import subprocess


class LoopDetector:
    """
    Detects when agent is stuck in loops.

    Detection methods:
    1. Repeated file reads (same files repeatedly) - with progress-aware tracking
    2. Session timeout (too long without progress)
    3. Repeated output patterns
    4. No tool calls (agent just talking)
    """

    def __init__(
        self,
        max_repeated_reads: int = 12,  # Increased from 3 to 12 to reduce false positives
        session_timeout_minutes: int = 60,
        progress_window_size: int = 5
    ):
        self.max_repeated_reads = max_repeated_reads
        self.session_timeout_minutes = session_timeout_minutes
        self.progress_window_size = progress_window_size

        self.session_start = None
        self.file_read_history = deque(maxlen=15)  # Increased history tracking
        self.write_history = deque(maxlen=10)  # Track writes for progress detection
        self.output_patterns = deque(maxlen=10)  # Last 10 outputs
        self.tool_call_count = 0
        self.last_tool_call_time = None
    
    def start_session(self):
        """Mark session start."""
        self.session_start = time.time()
        self.tool_call_count = 0
        self.last_tool_call_time = None
    
    def record_file_read(self, file_path: str):
        """Record a file being read."""
        self.tool_call_count += 1
        self.last_tool_call_time = time.time()

        # Add to current session's file list
        if not self.file_read_history or len(self.file_read_history[-1]) > 100:
            # Start new session tracking
            self.file_read_history.append([])

        self.file_read_history[-1].append(file_path)

    def record_file_write(self, file_path: str):
        """Record a file being written (indicates progress)."""
        self.tool_call_count += 1
        self.last_tool_call_time = time.time()
        self.write_history.append(file_path)
    
    def record_output(self, text: str):
        """Record agent output pattern."""
        # Normalize and store pattern
        pattern = text[:200].lower().strip()  # First 200 chars
        self.output_patterns.append(pattern)
    
    def check_repeated_file_reads(self) -> tuple[bool, str]:
        """
        Check if agent is reading same files repeatedly (progress-aware).

        Returns:
            (is_loop, reason)
        """
        if len(self.file_read_history) < self.max_repeated_reads:
            return False, ""

        # Get last N sessions of file reads
        recent_sessions = list(self.file_read_history)[-self.max_repeated_reads:]

        # Convert to sets for comparison
        file_sets = [set(session) for session in recent_sessions]

        # Check if same files in all sessions
        if len(file_sets) > 1:
            intersection = file_sets[0]
            for fs in file_sets[1:]:
                intersection = intersection & fs

            # If 80%+ overlap across sessions = potential loop
            overlap_ratio = len(intersection) / max(len(fs) for fs in file_sets)

            if overlap_ratio > 0.8:
                # BUT: If writes are happening, allow more reads (progress indicator)
                recent_writes = list(self.write_history)[-self.progress_window_size:]
                has_recent_progress = len(recent_writes) > 0

                if not has_recent_progress:
                    # No writes = stuck in read loop
                    common_files = list(intersection)[:5]
                    return True, f"Reading same files repeatedly without progress: {', '.join(common_files)}"
                # else: Writes happening, this is iterative work, allow it

        return False, ""
    
    def check_session_timeout(self) -> tuple[bool, str]:
        """
        Check if session has been running too long.
        
        Returns:
            (is_timeout, reason)
        """
        if not self.session_start:
            return False, ""
        
        elapsed = (time.time() - self.session_start) / 60  # minutes
        
        if elapsed > self.session_timeout_minutes:
            return True, f"Session timeout ({elapsed:.1f} minutes > {self.session_timeout_minutes} limit)"
        
        return False, ""
    
    def check_no_tool_calls(self) -> tuple[bool, str]:
        """
        Check if agent is just talking without using tools.
        
        Returns:
            (is_stuck, reason)
        """
        if not self.last_tool_call_time:
            # Just started, give it time
            if self.session_start and (time.time() - self.session_start) > 300:  # 5 minutes
                return True, "No tool calls in 5 minutes - agent just talking"
            return False, ""
        
        # Check time since last tool call
        time_since_tool = time.time() - self.last_tool_call_time
        
        if time_since_tool > 600:  # 10 minutes without tool call
            return True, "No tool calls in 10 minutes - agent stuck"
        
        return False, ""
    
    def check_repeated_output(self) -> tuple[bool, str]:
        """
        Check if agent is repeating same output.
        
        Returns:
            (is_loop, reason)
        """
        if len(self.output_patterns) < 5:
            return False, ""
        
        # Check last 5 outputs
        recent = list(self.output_patterns)[-5:]
        
        # If 4+ are very similar = loop
        unique_patterns = len(set(recent))
        
        if unique_patterns <= 2:
            return True, f"Repeating same output pattern ({unique_patterns} unique in last 5)"
        
        return False, ""
    
    def check_for_loop(self) -> tuple[bool, str]:
        """
        Master check - combines all detection methods.
        
        Returns:
            (is_stuck, reason)
        """
        # Check all methods
        checks = [
            self.check_repeated_file_reads(),
            self.check_session_timeout(),
            self.check_no_tool_calls(),
            self.check_repeated_output()
        ]
        
        for is_stuck, reason in checks:
            if is_stuck:
                return True, reason
        
        return False, "Agent progressing normally"
    
    def reset_session(self):
        """Reset for new session."""
        self.session_start = None
        self.tool_call_count = 0
        self.last_tool_call_time = None


def get_latest_commit(project_dir: Path) -> str:
    """Get latest git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except:
        return "unknown"


def has_uncommitted_changes(project_dir: Path) -> bool:
    """Check if there are uncommitted changes (means progress even without commit)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        return bool(result.stdout.strip())
    except:
        return False

