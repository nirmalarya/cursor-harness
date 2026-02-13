"""
Auto-recovery strategies for common failure scenarios.

Detects failure patterns and applies recovery strategies automatically.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class RecoveryStrategy(Enum):
    """Available recovery strategies."""
    CHECKPOINT_ROLLBACK = "checkpoint_rollback"
    REDUCE_SCOPE = "reduce_scope"
    SIMPLIFY_TASK = "simplify_task"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    SKIP_AND_CONTINUE = "skip_and_continue"
    FALLBACK_MODEL = "fallback_model"
    REDUCE_CONTEXT = "reduce_context"
    BREAK_INTO_SUBTASKS = "break_into_subtasks"


@dataclass
class RecoveryAction:
    """A recovery action taken."""
    action_id: str
    timestamp: str
    failure_type: str
    strategy: str
    parameters: Dict[str, Any]
    success: Optional[bool] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'RecoveryAction':
        return RecoveryAction(**data)


class AutoRecovery:
    """
    Automatic recovery system for handling failures.
    
    Monitors session health, detects failure patterns,
    and applies appropriate recovery strategies.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize auto-recovery system.
        
        Args:
            project_dir: Project directory
        """
        self.project_dir = Path(project_dir)
        self.recovery_dir = self.project_dir / ".cursor" / "recovery"
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        
        self.actions_file = self.recovery_dir / "actions.json"
        self.state_file = self.recovery_dir / "state.json"
        
        self.actions: List[RecoveryAction] = []
        self.state: Dict[str, Any] = {
            'consecutive_failures': 0,
            'last_success_time': None,
            'retry_count': 0,
            'current_strategy': None
        }
        
        self.strategy_handlers: Dict[str, Callable] = {}
        
        self._load_actions()
        self._load_state()
        self._register_default_strategies()
    
    def detect_and_recover(
        self,
        failure_type: str,
        context: Dict[str, Any]
    ) -> Optional[RecoveryAction]:
        """
        Detect failure pattern and apply recovery strategy.
        
        Args:
            failure_type: Type of failure (verification, timeout, loop, etc.)
            context: Context about the failure
        
        Returns:
            RecoveryAction if recovery attempted, None otherwise
        """
        # Update state
        self.state['consecutive_failures'] += 1
        
        # Determine strategy based on failure pattern
        strategy = self._select_strategy(failure_type, context)
        
        if not strategy:
            return None
        
        # Create recovery action
        action = RecoveryAction(
            action_id=f"{failure_type}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            failure_type=failure_type,
            strategy=strategy.value,
            parameters=context
        )
        
        # Execute strategy
        if strategy.value in self.strategy_handlers:
            try:
                result = self.strategy_handlers[strategy.value](context)
                action.success = result.get('success', False)
                action.notes = result.get('notes', '')
            except Exception as e:
                action.success = False
                action.notes = f"Strategy execution failed: {str(e)}"
        
        self.actions.append(action)
        self._save_actions()
        
        # Update state
        if action.success:
            self.state['consecutive_failures'] = 0
            self.state['last_success_time'] = time.time()
            self.state['retry_count'] = 0
        else:
            self.state['retry_count'] += 1
        
        self.state['current_strategy'] = strategy.value
        self._save_state()
        
        return action
    
    def _select_strategy(
        self,
        failure_type: str,
        context: Dict[str, Any]
    ) -> Optional[RecoveryStrategy]:
        """
        Select appropriate recovery strategy based on failure.
        
        Args:
            failure_type: Type of failure
            context: Failure context
        
        Returns:
            RecoveryStrategy or None
        """
        consecutive = self.state['consecutive_failures']
        retry_count = self.state['retry_count']
        
        # Escalating recovery strategies
        if failure_type == "verification_failure":
            if consecutive >= 3:
                return RecoveryStrategy.CHECKPOINT_ROLLBACK
            elif consecutive >= 2:
                return RecoveryStrategy.SIMPLIFY_TASK
            else:
                return RecoveryStrategy.RETRY_WITH_BACKOFF
        
        elif failure_type == "timeout":
            if retry_count >= 2:
                return RecoveryStrategy.REDUCE_SCOPE
            else:
                return RecoveryStrategy.RETRY_WITH_BACKOFF
        
        elif failure_type == "loop_detected":
            return RecoveryStrategy.BREAK_INTO_SUBTASKS
        
        elif failure_type == "context_overflow":
            return RecoveryStrategy.REDUCE_CONTEXT
        
        elif failure_type == "model_error":
            if retry_count >= 1:
                return RecoveryStrategy.FALLBACK_MODEL
            else:
                return RecoveryStrategy.RETRY_WITH_BACKOFF
        
        elif failure_type == "dependency_failure":
            if context.get('critical', False):
                return RecoveryStrategy.CHECKPOINT_ROLLBACK
            else:
                return RecoveryStrategy.SKIP_AND_CONTINUE
        
        elif failure_type == "resource_exhaustion":
            return RecoveryStrategy.REDUCE_SCOPE
        
        return None
    
    def register_strategy_handler(
        self,
        strategy: RecoveryStrategy,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        """
        Register a handler for a recovery strategy.
        
        Args:
            strategy: Recovery strategy
            handler: Function that executes the strategy
                    Returns dict with 'success' and optional 'notes'
        """
        self.strategy_handlers[strategy.value] = handler
    
    def _register_default_strategies(self):
        """Register default strategy handlers."""
        
        def checkpoint_rollback(context):
            print(f"\n   🔄 RECOVERY: Checkpoint rollback")
            print(f"      Consecutive failures: {self.state['consecutive_failures']}")
            print(f"      Action: Rolling back to last known-good checkpoint")
            return {'success': True, 'notes': 'Rollback suggested'}
        
        def reduce_scope(context):
            print(f"\n   📉 RECOVERY: Reduce scope")
            print(f"      Reason: {context.get('reason', 'Unknown')}")
            print(f"      Action: Break current task into smaller pieces")
            return {'success': True, 'notes': 'Scope reduction suggested'}
        
        def simplify_task(context):
            print(f"\n   🎯 RECOVERY: Simplify task")
            print(f"      Action: Remove optional requirements, focus on core functionality")
            return {'success': True, 'notes': 'Simplification suggested'}
        
        def retry_with_backoff(context):
            retry_count = self.state['retry_count']
            backoff = min(2 ** retry_count, 60)  # Exponential backoff, max 60s
            print(f"\n   🔁 RECOVERY: Retry with backoff")
            print(f"      Retry #{retry_count + 1}, backoff: {backoff}s")
            time.sleep(backoff)
            return {'success': True, 'notes': f'Retry after {backoff}s backoff'}
        
        def skip_and_continue(context):
            print(f"\n   ⏭️  RECOVERY: Skip and continue")
            print(f"      Skipping non-critical task, proceeding to next")
            return {'success': True, 'notes': 'Skipped failed task'}
        
        def fallback_model(context):
            print(f"\n   🔀 RECOVERY: Fallback model")
            print(f"      Switching to simpler/more reliable model")
            return {'success': True, 'notes': 'Model fallback suggested'}
        
        def reduce_context(context):
            print(f"\n   ✂️  RECOVERY: Reduce context")
            print(f"      Trimming context to fit within limits")
            return {'success': True, 'notes': 'Context reduction suggested'}
        
        def break_into_subtasks(context):
            print(f"\n   🧩 RECOVERY: Break into subtasks")
            print(f"      Decomposing complex task into manageable pieces")
            return {'success': True, 'notes': 'Task decomposition suggested'}
        
        self.register_strategy_handler(RecoveryStrategy.CHECKPOINT_ROLLBACK, checkpoint_rollback)
        self.register_strategy_handler(RecoveryStrategy.REDUCE_SCOPE, reduce_scope)
        self.register_strategy_handler(RecoveryStrategy.SIMPLIFY_TASK, simplify_task)
        self.register_strategy_handler(RecoveryStrategy.RETRY_WITH_BACKOFF, retry_with_backoff)
        self.register_strategy_handler(RecoveryStrategy.SKIP_AND_CONTINUE, skip_and_continue)
        self.register_strategy_handler(RecoveryStrategy.FALLBACK_MODEL, fallback_model)
        self.register_strategy_handler(RecoveryStrategy.REDUCE_CONTEXT, reduce_context)
        self.register_strategy_handler(RecoveryStrategy.BREAK_INTO_SUBTASKS, break_into_subtasks)
    
    def mark_success(self):
        """Mark that a recovery was successful."""
        self.state['consecutive_failures'] = 0
        self.state['retry_count'] = 0
        self.state['last_success_time'] = time.time()
        self._save_state()
    
    def get_stats(self) -> Dict:
        """Get recovery statistics."""
        total = len(self.actions)
        successful = sum(1 for a in self.actions if a.success)
        
        by_strategy = {}
        for action in self.actions:
            by_strategy[action.strategy] = by_strategy.get(action.strategy, 0) + 1
        
        by_failure = {}
        for action in self.actions:
            by_failure[action.failure_type] = by_failure.get(action.failure_type, 0) + 1
        
        return {
            'total_recoveries': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total if total > 0 else 0.0,
            'by_strategy': by_strategy,
            'by_failure_type': by_failure,
            'current_state': self.state.copy()
        }
    
    def get_recent_actions(self, limit: int = 10) -> List[RecoveryAction]:
        """Get recent recovery actions."""
        return self.actions[-limit:]
    
    def _load_actions(self):
        """Load actions from disk."""
        if not self.actions_file.exists():
            return
        
        try:
            with open(self.actions_file, 'r') as f:
                data = json.load(f)
                self.actions = [RecoveryAction.from_dict(a) for a in data]
        except:
            pass
    
    def _save_actions(self):
        """Save actions to disk."""
        try:
            with open(self.actions_file, 'w') as f:
                json.dump(
                    [a.to_dict() for a in self.actions],
                    f,
                    indent=2
                )
        except:
            pass
    
    def _load_state(self):
        """Load state from disk."""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                self.state.update(json.load(f))
        except:
            pass
    
    def _save_state(self):
        """Save state to disk."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except:
            pass
