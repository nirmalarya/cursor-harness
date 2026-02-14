"""
Multi-agent coordination for cursor-harness.

Enables multiple harness instances to work together on complex tasks.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """A task for an agent."""
    task_id: str
    agent_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = AgentStatus.PENDING.value
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'AgentTask':
        return AgentTask(**data)


@dataclass
class AgentMessage:
    """Message between agents."""
    message_id: str
    from_agent: str
    to_agent: str
    content: Any
    timestamp: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'AgentMessage':
        return AgentMessage(**data)


class MultiAgentCoordinator:
    """
    Coordinates multiple cursor-harness agents.
    
    Manages task distribution, dependencies, message passing,
    and result aggregation across multiple agents.
    """
    
    def __init__(self, project_dir: Path, coordinator_id: Optional[str] = None):
        """
        Initialize multi-agent coordinator.
        
        Args:
            project_dir: Project directory
            coordinator_id: Optional coordinator ID (auto-generated if not provided)
        """
        self.project_dir = Path(project_dir)
        self.coordinator_id = coordinator_id or self._generate_id()
        
        self.coordination_dir = self.project_dir / ".cursor" / "coordination"
        self.coordination_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks_file = self.coordination_dir / f"{self.coordinator_id}_tasks.json"
        self.messages_file = self.coordination_dir / f"{self.coordinator_id}_messages.json"
        
        self.tasks: Dict[str, AgentTask] = {}
        self.messages: List[AgentMessage] = []
        self.agents: Dict[str, Dict[str, Any]] = {}
        
        self._load_state()
    
    def register_agent(self, agent_id: str, capabilities: Optional[List[str]] = None):
        """
        Register an agent with the coordinator.
        
        Args:
            agent_id: Agent identifier
            capabilities: Optional list of agent capabilities
        """
        self.agents[agent_id] = {
            'agent_id': agent_id,
            'capabilities': capabilities or [],
            'registered_at': time.time(),
            'task_count': 0
        }
    
    def create_task(
        self,
        task_id: str,
        description: str,
        agent_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> AgentTask:
        """
        Create a task for an agent.
        
        Args:
            task_id: Task identifier
            description: Task description
            agent_id: Agent to assign (auto-assigned if None)
            dependencies: Task dependencies (other task IDs)
        
        Returns:
            AgentTask
        """
        if not agent_id:
            agent_id = self._assign_agent(description)
        
        task = AgentTask(
            task_id=task_id,
            agent_id=agent_id,
            description=description,
            dependencies=dependencies or []
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        return task
    
    def start_task(self, task_id: str):
        """
        Mark task as started.
        
        Args:
            task_id: Task ID
        """
        if task_id in self.tasks:
            self.tasks[task_id].status = AgentStatus.RUNNING.value
            self.tasks[task_id].started_at = time.time()
            self._save_tasks()
    
    def complete_task(self, task_id: str, result: Any):
        """
        Mark task as completed with result.
        
        Args:
            task_id: Task ID
            result: Task result
        """
        if task_id in self.tasks:
            self.tasks[task_id].status = AgentStatus.COMPLETED.value
            self.tasks[task_id].result = result
            self.tasks[task_id].completed_at = time.time()
            self._save_tasks()
    
    def fail_task(self, task_id: str, error: str):
        """
        Mark task as failed.
        
        Args:
            task_id: Task ID
            error: Error message
        """
        if task_id in self.tasks:
            self.tasks[task_id].status = AgentStatus.FAILED.value
            self.tasks[task_id].error = error
            self.tasks[task_id].completed_at = time.time()
            self._save_tasks()
    
    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        content: Any
    ) -> AgentMessage:
        """
        Send message from one agent to another.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Receiver agent ID
            content: Message content
        
        Returns:
            AgentMessage
        """
        message = AgentMessage(
            message_id=self._generate_id(),
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            timestamp=time.time()
        )
        
        self.messages.append(message)
        self._save_messages()
        
        return message
    
    def get_messages_for_agent(self, agent_id: str) -> List[AgentMessage]:
        """
        Get all messages for an agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            List of messages
        """
        return [m for m in self.messages if m.to_agent == agent_id]
    
    def get_ready_tasks(self) -> List[AgentTask]:
        """
        Get tasks that are ready to execute (dependencies satisfied).
        
        Returns:
            List of ready tasks
        """
        ready = []
        for task in self.tasks.values():
            if task.status != AgentStatus.PENDING.value:
                continue
            
            # Check if all dependencies are completed
            deps_satisfied = all(
                self.tasks.get(dep_id, AgentTask("", "", "")).status == AgentStatus.COMPLETED.value
                for dep_id in task.dependencies
            )
            
            if deps_satisfied:
                ready.append(task)
        
        return ready
    
    def get_tasks_for_agent(self, agent_id: str) -> List[AgentTask]:
        """
        Get all tasks assigned to an agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            List of tasks
        """
        return [t for t in self.tasks.values() if t.agent_id == agent_id]
    
    def get_task_results(self, task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get results from completed tasks.
        
        Args:
            task_ids: Optional list of task IDs (all completed if None)
        
        Returns:
            Dict of task_id -> result
        """
        if task_ids:
            tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]
        else:
            tasks = self.tasks.values()
        
        return {
            task.task_id: task.result
            for task in tasks
            if task.status == AgentStatus.COMPLETED.value
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get coordinator status.
        
        Returns:
            Status dict
        """
        total_tasks = len(self.tasks)
        by_status = {}
        for task in self.tasks.values():
            by_status[task.status] = by_status.get(task.status, 0) + 1
        
        return {
            'coordinator_id': self.coordinator_id,
            'total_agents': len(self.agents),
            'total_tasks': total_tasks,
            'by_status': by_status,
            'total_messages': len(self.messages),
            'agents': list(self.agents.keys())
        }
    
    def _assign_agent(self, description: str) -> str:
        """
        Auto-assign agent based on description.
        
        For now, uses round-robin. Could be enhanced with
        capability matching.
        
        Args:
            description: Task description
        
        Returns:
            Agent ID
        """
        if not self.agents:
            # Create default agent
            default_id = "agent-0"
            self.register_agent(default_id)
            return default_id
        
        # Round-robin assignment
        agent_tasks = {aid: 0 for aid in self.agents}
        for task in self.tasks.values():
            if task.agent_id in agent_tasks:
                agent_tasks[task.agent_id] += 1
        
        # Assign to agent with fewest tasks
        return min(agent_tasks.items(), key=lambda x: x[1])[0]
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        content = f"{time.time()}_{id(self)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _load_state(self):
        """Load coordinator state from disk."""
        # Load tasks
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = {
                        tid: AgentTask.from_dict(tdata)
                        for tid, tdata in data.items()
                    }
            except:
                pass
        
        # Load messages
        if self.messages_file.exists():
            try:
                with open(self.messages_file, 'r') as f:
                    data = json.load(f)
                    self.messages = [AgentMessage.from_dict(m) for m in data]
            except:
                pass
    
    def _save_tasks(self):
        """Save tasks to disk."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(
                    {tid: t.to_dict() for tid, t in self.tasks.items()},
                    f,
                    indent=2
                )
        except:
            pass
    
    def _save_messages(self):
        """Save messages to disk."""
        try:
            with open(self.messages_file, 'w') as f:
                json.dump(
                    [m.to_dict() for m in self.messages],
                    f,
                    indent=2
                )
        except:
            pass
