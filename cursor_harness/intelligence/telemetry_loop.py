"""
Telemetry collection and action loop.

Collects session metrics, detects patterns, triggers corrective actions.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class TelemetryEvent:
    """A single telemetry event."""
    event_type: str
    timestamp: float
    session_id: str
    iteration: int
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'TelemetryEvent':
        return TelemetryEvent(**data)


@dataclass
class ActionTrigger:
    """An action triggered by telemetry analysis."""
    trigger_id: str
    timestamp: str
    condition: str
    action_type: str
    action_params: Dict[str, Any]
    executed: bool = False
    success: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'ActionTrigger':
        return ActionTrigger(**data)


class TelemetryLoop:
    """
    Telemetry collection and action triggering system.
    
    Collects metrics during sessions, analyzes patterns,
    and triggers corrective actions automatically.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize telemetry loop.
        
        Args:
            project_dir: Project directory
        """
        self.project_dir = Path(project_dir)
        self.telemetry_dir = self.project_dir / ".cursor" / "telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        self.events_file = self.telemetry_dir / "events.jsonl"
        self.triggers_file = self.telemetry_dir / "triggers.json"
        
        self.events: List[TelemetryEvent] = []
        self.triggers: List[ActionTrigger] = []
        
        self.action_handlers: Dict[str, Callable] = {}
        
        self._load_triggers()
        self._register_default_handlers()
    
    def record(
        self,
        event_type: str,
        session_id: str,
        iteration: int,
        **data
    ):
        """
        Record a telemetry event.
        
        Args:
            event_type: Type of event (error, performance, verification, etc.)
            session_id: Session identifier
            iteration: Current iteration
            **data: Event-specific data
        """
        event = TelemetryEvent(
            event_type=event_type,
            timestamp=time.time(),
            session_id=session_id,
            iteration=iteration,
            data=data
        )
        
        self.events.append(event)
        self._append_event(event)
        
        # Analyze and potentially trigger actions
        self._analyze_and_trigger()
    
    def _append_event(self, event: TelemetryEvent):
        """Append event to JSONL file."""
        try:
            with open(self.events_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
        except:
            pass
    
    def _analyze_and_trigger(self):
        """Analyze recent events and trigger actions if needed."""
        # Check for patterns in recent events
        recent = self.events[-50:]  # Last 50 events
        
        # Pattern 1: High error rate
        error_count = sum(1 for e in recent if e.event_type == 'error')
        if error_count > 10:
            self._trigger_action(
                condition="high_error_rate",
                action_type="reduce_complexity",
                action_params={'reason': f'{error_count} errors in last 50 events'}
            )
        
        # Pattern 2: Consecutive verification failures
        verif_events = [e for e in recent if e.event_type == 'verification']
        if len(verif_events) >= 3:
            last_three = verif_events[-3:]
            if all(not e.data.get('passed', True) for e in last_three):
                self._trigger_action(
                    condition="consecutive_verification_failures",
                    action_type="rollback_checkpoint",
                    action_params={'failures': 3}
                )
        
        # Pattern 3: Slow iterations
        perf_events = [e for e in recent if e.event_type == 'performance']
        if len(perf_events) >= 5:
            avg_duration = sum(e.data.get('duration', 0) for e in perf_events) / len(perf_events)
            if avg_duration > 300:  # >5 minutes avg
                self._trigger_action(
                    condition="slow_iterations",
                    action_type="optimize_prompts",
                    action_params={'avg_duration': avg_duration}
                )
        
        # Pattern 4: Token limit warnings
        token_events = [e for e in recent if e.event_type == 'token_warning']
        if len(token_events) > 3:
            self._trigger_action(
                condition="frequent_token_warnings",
                action_type="reduce_context",
                action_params={'warning_count': len(token_events)}
            )
    
    def _trigger_action(
        self,
        condition: str,
        action_type: str,
        action_params: Dict[str, Any]
    ):
        """
        Trigger a corrective action.
        
        Args:
            condition: What triggered this action
            action_type: Type of action to take
            action_params: Parameters for the action
        """
        # Check if already triggered recently
        recent_triggers = []
        for t in self.triggers:
            if t.condition == condition:
                try:
                    # Parse ISO timestamp
                    from datetime import datetime as dt
                    trigger_time = dt.fromisoformat(t.timestamp.replace('Z', '+00:00'))
                    age_seconds = (dt.now(trigger_time.tzinfo) - trigger_time).total_seconds()
                    if age_seconds < 3600:  # Within last hour
                        recent_triggers.append(t)
                except:
                    pass
        
        if recent_triggers:
            return  # Don't spam same action
        
        trigger = ActionTrigger(
            trigger_id=f"{condition}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            condition=condition,
            action_type=action_type,
            action_params=action_params,
            executed=False
        )
        
        self.triggers.append(trigger)
        self._save_triggers()
        
        # Execute action if handler registered
        if action_type in self.action_handlers:
            try:
                self.action_handlers[action_type](action_params)
                trigger.executed = True
                trigger.success = True
            except Exception as e:
                trigger.executed = True
                trigger.success = False
                trigger.action_params['error'] = str(e)
            
            self._save_triggers()
    
    def register_action_handler(
        self,
        action_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ):
        """
        Register a handler for an action type.
        
        Args:
            action_type: Type of action
            handler: Function that takes action_params and executes the action
        """
        self.action_handlers[action_type] = handler
    
    def _register_default_handlers(self):
        """Register default action handlers."""
        
        def reduce_complexity(params):
            """Suggest reducing task complexity."""
            print(f"\n   ⚡ ACTION: Reduce complexity - {params.get('reason', 'unknown')}")
            print(f"      Suggestion: Break down current task into smaller subtasks")
        
        def rollback_checkpoint(params):
            """Trigger checkpoint rollback."""
            print(f"\n   ⚡ ACTION: Rollback suggested - {params.get('failures', 0)} consecutive failures")
            print(f"      Consider rolling back to last known-good checkpoint")
        
        def optimize_prompts(params):
            """Suggest prompt optimization."""
            avg_dur = params.get('avg_duration', 0)
            print(f"\n   ⚡ ACTION: Optimize prompts - avg iteration time: {avg_dur:.1f}s")
            print(f"      Suggestion: Reduce prompt verbosity or context size")
        
        def reduce_context(params):
            """Suggest context reduction."""
            count = params.get('warning_count', 0)
            print(f"\n   ⚡ ACTION: Reduce context - {count} token warnings")
            print(f"      Suggestion: Trim feature list or use continuation mode")
        
        self.register_action_handler('reduce_complexity', reduce_complexity)
        self.register_action_handler('rollback_checkpoint', rollback_checkpoint)
        self.register_action_handler('optimize_prompts', optimize_prompts)
        self.register_action_handler('reduce_context', reduce_context)
    
    def get_stats(self) -> Dict:
        """Get telemetry statistics."""
        if not self.events:
            return {
                'total_events': 0,
                'by_type': {},
                'triggers': 0
            }
        
        by_type = defaultdict(int)
        for event in self.events:
            by_type[event.event_type] += 1
        
        return {
            'total_events': len(self.events),
            'by_type': dict(by_type),
            'triggers': len(self.triggers),
            'executed_triggers': sum(1 for t in self.triggers if t.executed),
            'successful_triggers': sum(1 for t in self.triggers if t.success)
        }
    
    def get_recent_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[TelemetryEvent]:
        """
        Get recent events, optionally filtered by type.
        
        Args:
            event_type: Optional event type filter
            limit: Max events to return
        
        Returns:
            List of recent events
        """
        events = self.events[-limit * 2:]  # Get extra for filtering
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def get_triggers(
        self,
        executed_only: bool = False
    ) -> List[ActionTrigger]:
        """Get action triggers, optionally filtered."""
        if executed_only:
            return [t for t in self.triggers if t.executed]
        return self.triggers.copy()
    
    def _load_triggers(self):
        """Load triggers from disk."""
        if not self.triggers_file.exists():
            return
        
        try:
            with open(self.triggers_file, 'r') as f:
                data = json.load(f)
                self.triggers = [ActionTrigger.from_dict(t) for t in data]
        except:
            pass
    
    def _save_triggers(self):
        """Save triggers to disk."""
        try:
            with open(self.triggers_file, 'w') as f:
                json.dump(
                    [t.to_dict() for t in self.triggers],
                    f,
                    indent=2
                )
        except:
            pass
