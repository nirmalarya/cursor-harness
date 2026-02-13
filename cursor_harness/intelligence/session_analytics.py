"""
Session analytics dashboard.

Aggregates metrics across sessions for insights and trends.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class AnalyticsSummary:
    """Analytics summary across sessions."""
    total_sessions: int
    total_duration: float
    avg_duration: float
    success_rate: float
    total_errors: int
    total_recoveries: int
    top_operations: List[Dict[str, Any]]
    trends: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SessionAnalytics:
    """
    Analytics dashboard for cursor-harness sessions.
    
    Aggregates data from profiling, telemetry, checkpoints,
    recovery actions, and patterns to provide insights.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize analytics dashboard.
        
        Args:
            project_dir: Project directory
        """
        self.project_dir = Path(project_dir)
        self.cursor_dir = self.project_dir / ".cursor"
        
        self.profiling_dir = self.cursor_dir / "profiling"
        self.telemetry_dir = self.cursor_dir / "telemetry"
        self.checkpoints_dir = self.cursor_dir / "checkpoints"
        self.recovery_dir = self.cursor_dir / "recovery"
        self.intelligence_dir = self.cursor_dir / "intelligence"
    
    def get_summary(self) -> AnalyticsSummary:
        """
        Get high-level analytics summary.
        
        Returns:
            AnalyticsSummary
        """
        # Load all profiles
        profiles = self._load_all_profiles()
        
        if not profiles:
            return AnalyticsSummary(
                total_sessions=0,
                total_duration=0.0,
                avg_duration=0.0,
                success_rate=0.0,
                total_errors=0,
                total_recoveries=0,
                top_operations=[],
                trends={}
            )
        
        # Compute metrics
        total_sessions = len(profiles)
        total_duration = sum(p.get('total_duration', 0) for p in profiles)
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
        
        # Count errors from telemetry
        total_errors = self._count_total_errors()
        
        # Count recoveries
        total_recoveries = self._count_total_recoveries()
        
        # Success rate (sessions without critical failures)
        success_rate = self._compute_success_rate(profiles)
        
        # Top operations by total time
        top_operations = self._get_top_operations(profiles, limit=10)
        
        # Trends
        trends = self._compute_trends(profiles)
        
        return AnalyticsSummary(
            total_sessions=total_sessions,
            total_duration=total_duration,
            avg_duration=avg_duration,
            success_rate=success_rate,
            total_errors=total_errors,
            total_recoveries=total_recoveries,
            top_operations=top_operations,
            trends=trends
        )
    
    def get_operation_trends(self, operation: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get trends for a specific operation across sessions.
        
        Args:
            operation: Operation name
            limit: Max sessions to include
        
        Returns:
            Trends dict with session_ids, durations, counts
        """
        profiles = self._load_all_profiles()
        
        sessions = []
        durations = []
        counts = []
        
        for profile in profiles[-limit:]:
            by_op = profile.get('summary', {}).get('by_operation', {})
            if operation in by_op:
                sessions.append(profile['session_id'])
                durations.append(by_op[operation]['avg'])
                counts.append(by_op[operation]['count'])
        
        return {
            'operation': operation,
            'sessions': sessions,
            'avg_durations': durations,
            'counts': counts,
            'trend_direction': self._compute_trend_direction(durations)
        }
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Analyze error patterns across sessions.
        
        Returns:
            Error analysis with counts by type, trends
        """
        events = self._load_telemetry_events()
        
        error_events = [e for e in events if e.get('event_type') == 'error']
        
        by_type = defaultdict(int)
        by_session = defaultdict(int)
        
        for event in error_events:
            error_type = event.get('data', {}).get('type', 'unknown')
            session_id = event.get('session_id', 'unknown')
            by_type[error_type] += 1
            by_session[session_id] += 1
        
        return {
            'total_errors': len(error_events),
            'by_type': dict(by_type),
            'by_session': dict(by_session),
            'most_common': sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def get_recovery_effectiveness(self) -> Dict[str, Any]:
        """
        Analyze recovery strategy effectiveness.
        
        Returns:
            Recovery effectiveness metrics
        """
        if not self.recovery_dir.exists():
            return {'total_recoveries': 0}
        
        actions_file = self.recovery_dir / "actions.json"
        if not actions_file.exists():
            return {'total_recoveries': 0}
        
        try:
            with open(actions_file, 'r') as f:
                actions = json.load(f)
        except:
            return {'total_recoveries': 0}
        
        total = len(actions)
        successful = sum(1 for a in actions if a.get('success'))
        
        by_strategy = defaultdict(lambda: {'total': 0, 'successful': 0})
        for action in actions:
            strategy = action.get('strategy', 'unknown')
            by_strategy[strategy]['total'] += 1
            if action.get('success'):
                by_strategy[strategy]['successful'] += 1
        
        # Compute success rate per strategy
        strategy_rates = {}
        for strategy, stats in by_strategy.items():
            strategy_rates[strategy] = {
                'total': stats['total'],
                'successful': stats['successful'],
                'success_rate': stats['successful'] / stats['total'] if stats['total'] > 0 else 0
            }
        
        return {
            'total_recoveries': total,
            'successful_recoveries': successful,
            'success_rate': successful / total if total > 0 else 0,
            'by_strategy': strategy_rates,
            'most_effective': sorted(
                strategy_rates.items(),
                key=lambda x: x[1]['success_rate'],
                reverse=True
            )[:3]
        }
    
    def get_checkpoint_stats(self) -> Dict[str, Any]:
        """
        Get checkpoint statistics.
        
        Returns:
            Checkpoint stats
        """
        if not self.checkpoints_dir.exists():
            return {'total_checkpoints': 0}
        
        total_checkpoints = 0
        rollbacks = 0
        
        for checkpoint_file in self.checkpoints_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoints = json.load(f)
                    total_checkpoints += len(checkpoints)
                    # Count potential rollbacks (failed checkpoints)
                    rollbacks += sum(1 for cp in checkpoints if not cp.get('verification_passed', True))
            except:
                pass
        
        return {
            'total_checkpoints': total_checkpoints,
            'potential_rollbacks': rollbacks,
            'success_rate': (total_checkpoints - rollbacks) / total_checkpoints if total_checkpoints > 0 else 0
        }
    
    def export_report(self, output_path: Optional[Path] = None) -> str:
        """
        Export analytics report to JSON.
        
        Args:
            output_path: Optional output path
        
        Returns:
            JSON string
        """
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': self.get_summary().to_dict(),
            'error_analysis': self.get_error_analysis(),
            'recovery_effectiveness': self.get_recovery_effectiveness(),
            'checkpoint_stats': self.get_checkpoint_stats()
        }
        
        json_str = json.dumps(report, indent=2)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def _load_all_profiles(self) -> List[Dict]:
        """Load all session profiles."""
        if not self.profiling_dir.exists():
            return []
        
        profiles = []
        for profile_file in self.profiling_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    profiles.append(json.load(f))
            except:
                pass
        
        return profiles
    
    def _load_telemetry_events(self) -> List[Dict]:
        """Load all telemetry events."""
        if not self.telemetry_dir.exists():
            return []
        
        events_file = self.telemetry_dir / "events.jsonl"
        if not events_file.exists():
            return []
        
        events = []
        try:
            with open(events_file, 'r') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except:
            pass
        
        return events
    
    def _count_total_errors(self) -> int:
        """Count total errors from telemetry."""
        events = self._load_telemetry_events()
        return sum(1 for e in events if e.get('event_type') == 'error')
    
    def _count_total_recoveries(self) -> int:
        """Count total recovery actions."""
        if not self.recovery_dir.exists():
            return 0
        
        actions_file = self.recovery_dir / "actions.json"
        if not actions_file.exists():
            return 0
        
        try:
            with open(actions_file, 'r') as f:
                actions = json.load(f)
                return len(actions)
        except:
            return 0
    
    def _compute_success_rate(self, profiles: List[Dict]) -> float:
        """Compute overall success rate."""
        if not profiles:
            return 0.0
        
        # Consider a session successful if it completed without critical errors
        # For now, just check if it has a valid total_duration
        successful = sum(1 for p in profiles if p.get('total_duration') is not None)
        return successful / len(profiles)
    
    def _get_top_operations(self, profiles: List[Dict], limit: int) -> List[Dict[str, Any]]:
        """Get top operations by total time."""
        operation_totals = defaultdict(float)
        operation_counts = defaultdict(int)
        
        for profile in profiles:
            by_op = profile.get('summary', {}).get('by_operation', {})
            for op_name, stats in by_op.items():
                operation_totals[op_name] += stats.get('total', 0)
                operation_counts[op_name] += stats.get('count', 0)
        
        top = sorted(operation_totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'operation': op,
                'total_time': total,
                'count': operation_counts[op],
                'avg_time': total / operation_counts[op] if operation_counts[op] > 0 else 0
            }
            for op, total in top
        ]
    
    def _compute_trends(self, profiles: List[Dict]) -> Dict[str, Any]:
        """Compute trends over time."""
        if len(profiles) < 2:
            return {}
        
        # Sort by start_time
        sorted_profiles = sorted(profiles, key=lambda p: p.get('start_time', 0))
        
        # Duration trend
        durations = [p.get('total_duration', 0) for p in sorted_profiles if p.get('total_duration')]
        duration_trend = self._compute_trend_direction(durations)
        
        return {
            'duration': {
                'direction': duration_trend,
                'recent_avg': sum(durations[-5:]) / min(5, len(durations)) if durations else 0
            }
        }
    
    def _compute_trend_direction(self, values: List[float]) -> str:
        """
        Compute trend direction from values.
        
        Returns:
            'improving', 'declining', or 'stable'
        """
        if len(values) < 2:
            return 'stable'
        
        # Simple trend: compare first half vs second half
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(values[mid:]) / (len(values) - mid) if len(values) > mid else 0
        
        if second_half_avg < first_half_avg * 0.9:  # >10% improvement
            return 'improving'
        elif second_half_avg > first_half_avg * 1.1:  # >10% decline
            return 'declining'
        else:
            return 'stable'
