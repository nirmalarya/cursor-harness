"""
Performance profiling for cursor-harness sessions.

Tracks timing, resource usage, and throughput metrics.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from contextlib import contextmanager


@dataclass
class ProfileMetric:
    """A single performance metric."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self):
        """Mark metric as complete."""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'ProfileMetric':
        return ProfileMetric(**data)


@dataclass
class SessionProfile:
    """Performance profile for a session."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    metrics: List[ProfileMetric] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self):
        """Mark session as complete."""
        if self.end_time is None:
            self.end_time = time.time()
            self.total_duration = self.end_time - self.start_time
            self._compute_summary()
    
    def _compute_summary(self):
        """Compute summary statistics."""
        if not self.metrics:
            return
        
        by_name = {}
        for metric in self.metrics:
            if metric.duration is not None:
                if metric.name not in by_name:
                    by_name[metric.name] = []
                by_name[metric.name].append(metric.duration)
        
        self.summary = {
            'total_metrics': len(self.metrics),
            'total_duration': self.total_duration,
            'by_operation': {}
        }
        
        for name, durations in by_name.items():
            self.summary['by_operation'][name] = {
                'count': len(durations),
                'total': sum(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations)
            }
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_duration': self.total_duration,
            'metrics': [m.to_dict() for m in self.metrics],
            'summary': self.summary
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'SessionProfile':
        profile = SessionProfile(
            session_id=data['session_id'],
            start_time=data['start_time'],
            end_time=data.get('end_time'),
            total_duration=data.get('total_duration'),
            summary=data.get('summary', {})
        )
        profile.metrics = [ProfileMetric.from_dict(m) for m in data.get('metrics', [])]
        return profile


class PerformanceProfiler:
    """
    Performance profiler for cursor-harness sessions.
    
    Instruments operations and tracks timing/resource metrics.
    """
    
    def __init__(self, project_dir: Path, session_id: str):
        """
        Initialize profiler.
        
        Args:
            project_dir: Project directory
            session_id: Session identifier
        """
        self.project_dir = Path(project_dir)
        self.profiling_dir = self.project_dir / ".cursor" / "profiling"
        self.profiling_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = session_id
        self.profile = SessionProfile(
            session_id=session_id,
            start_time=time.time()
        )
        
        self.current_metrics: Dict[str, ProfileMetric] = {}
    
    @contextmanager
    def measure(self, operation: str, **metadata):
        """
        Context manager for measuring operation timing.
        
        Usage:
            with profiler.measure("llm_call", model="gpt-4"):
                # do work
                pass
        
        Args:
            operation: Operation name
            **metadata: Additional metadata to record
        """
        metric = ProfileMetric(
            name=operation,
            start_time=time.time(),
            metadata=metadata
        )
        
        try:
            yield metric
        finally:
            metric.complete()
            self.profile.metrics.append(metric)
    
    def start_metric(self, name: str, **metadata) -> str:
        """
        Start a metric (for non-context-manager usage).
        
        Args:
            name: Metric name
            **metadata: Additional metadata
        
        Returns:
            Metric key for later stopping
        """
        key = f"{name}_{len(self.current_metrics)}"
        metric = ProfileMetric(
            name=name,
            start_time=time.time(),
            metadata=metadata
        )
        self.current_metrics[key] = metric
        return key
    
    def stop_metric(self, key: str):
        """
        Stop a metric.
        
        Args:
            key: Metric key from start_metric
        """
        if key in self.current_metrics:
            metric = self.current_metrics.pop(key)
            metric.complete()
            self.profile.metrics.append(metric)
    
    def record_point(self, name: str, value: float, **metadata):
        """
        Record a point-in-time metric.
        
        Args:
            name: Metric name
            value: Metric value
            **metadata: Additional metadata
        """
        metric = ProfileMetric(
            name=name,
            start_time=time.time(),
            end_time=time.time(),
            duration=value,
            metadata=metadata
        )
        self.profile.metrics.append(metric)
    
    def complete_session(self):
        """Mark session as complete and compute summary."""
        self.profile.complete()
        self.save()
    
    def save(self):
        """Save profile to disk."""
        profile_file = self.profiling_dir / f"{self.session_id}.json"
        try:
            with open(profile_file, 'w') as f:
                json.dump(self.profile.to_dict(), f, indent=2)
        except:
            pass
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.profile.summary:
            self.profile._compute_summary()
        return self.profile.summary
    
    def get_slowest_operations(self, limit: int = 10) -> List[ProfileMetric]:
        """
        Get slowest operations.
        
        Args:
            limit: Max operations to return
        
        Returns:
            List of slowest metrics
        """
        completed = [m for m in self.profile.metrics if m.duration is not None]
        return sorted(completed, key=lambda m: m.duration, reverse=True)[:limit]
    
    def get_operation_stats(self, operation: str) -> Optional[Dict]:
        """
        Get statistics for a specific operation.
        
        Args:
            operation: Operation name
        
        Returns:
            Stats dict or None if operation not found
        """
        if not self.profile.summary:
            self.profile._compute_summary()
        
        return self.profile.summary.get('by_operation', {}).get(operation)
    
    @staticmethod
    def load_session(project_dir: Path, session_id: str) -> Optional['PerformanceProfiler']:
        """
        Load a saved session profile.
        
        Args:
            project_dir: Project directory
            session_id: Session ID
        
        Returns:
            PerformanceProfiler or None
        """
        profiling_dir = Path(project_dir) / ".cursor" / "profiling"
        profile_file = profiling_dir / f"{session_id}.json"
        
        if not profile_file.exists():
            return None
        
        try:
            with open(profile_file, 'r') as f:
                data = json.load(f)
                profile = SessionProfile.from_dict(data)
                
                profiler = PerformanceProfiler(project_dir, session_id)
                profiler.profile = profile
                return profiler
        except:
            return None
    
    @staticmethod
    def get_all_sessions(project_dir: Path) -> List[str]:
        """
        Get list of all profiled sessions.
        
        Args:
            project_dir: Project directory
        
        Returns:
            List of session IDs
        """
        profiling_dir = Path(project_dir) / ".cursor" / "profiling"
        if not profiling_dir.exists():
            return []
        
        sessions = []
        for profile_file in profiling_dir.glob("*.json"):
            sessions.append(profile_file.stem)
        
        return sessions
    
    @staticmethod
    def compare_sessions(
        project_dir: Path,
        session_id1: str,
        session_id2: str
    ) -> Dict[str, Any]:
        """
        Compare two session profiles.
        
        Args:
            project_dir: Project directory
            session_id1: First session ID
            session_id2: Second session ID
        
        Returns:
            Comparison dict
        """
        prof1 = PerformanceProfiler.load_session(project_dir, session_id1)
        prof2 = PerformanceProfiler.load_session(project_dir, session_id2)
        
        if not prof1 or not prof2:
            return {}
        
        sum1 = prof1.get_summary()
        sum2 = prof2.get_summary()
        
        comparison = {
            'session1': {
                'id': session_id1,
                'total_duration': sum1.get('total_duration'),
                'total_metrics': sum1.get('total_metrics')
            },
            'session2': {
                'id': session_id2,
                'total_duration': sum2.get('total_duration'),
                'total_metrics': sum2.get('total_metrics')
            },
            'differences': {}
        }
        
        # Compare common operations
        ops1 = set(sum1.get('by_operation', {}).keys())
        ops2 = set(sum2.get('by_operation', {}).keys())
        common = ops1 & ops2
        
        for op in common:
            stats1 = sum1['by_operation'][op]
            stats2 = sum2['by_operation'][op]
            
            comparison['differences'][op] = {
                'avg_duration_diff': stats2['avg'] - stats1['avg'],
                'count_diff': stats2['count'] - stats1['count'],
                'session1_avg': stats1['avg'],
                'session2_avg': stats2['avg']
            }
        
        return comparison
