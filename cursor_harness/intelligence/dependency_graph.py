"""
Feature dependency graph for task ordering.

Builds and maintains a dependency graph so tasks execute in
correct order and blockers are identified proactively.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque


@dataclass
class TaskNode:
    """A node in the dependency graph."""
    task_id: str
    title: str
    description: str
    dependencies: Set[str] = field(default_factory=set)  # IDs of tasks this depends on
    blocked_by: Set[str] = field(default_factory=set)  # Currently blocking tasks
    completed: bool = False
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['dependencies'] = list(self.dependencies)
        d['blocked_by'] = list(self.blocked_by)
        return d
    
    @staticmethod
    def from_dict(data: Dict) -> 'TaskNode':
        data['dependencies'] = set(data.get('dependencies', []))
        data['blocked_by'] = set(data.get('blocked_by', []))
        return TaskNode(**data)


class DependencyGraph:
    """
    Manages task dependencies and execution order.
    
    Provides topological sorting, blocker detection, and
    dependency visualization.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize dependency graph.
        
        Args:
            project_dir: Project directory
        """
        self.project_dir = Path(project_dir)
        self.graph_dir = self.project_dir / ".cursor" / "dependencies"
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        
        self.graph_file = self.graph_dir / "graph.json"
        
        self.tasks: Dict[str, TaskNode] = {}
        self._load()
    
    def add_task(
        self,
        task_id: str,
        title: str,
        description: str,
        dependencies: Optional[List[str]] = None
    ) -> TaskNode:
        """
        Add a task to the graph.
        
        Args:
            task_id: Unique task identifier
            title: Task title
            description: Task description
            dependencies: List of task IDs this task depends on
        
        Returns:
            TaskNode
        """
        task = TaskNode(
            task_id=task_id,
            title=title,
            description=description,
            dependencies=set(dependencies or []),
            completed=False
        )
        
        # Update blocked_by for dependencies
        task.blocked_by = {dep for dep in task.dependencies if not self.tasks.get(dep, TaskNode("", "", "")).completed}
        
        self.tasks[task_id] = task
        self._save()
        
        return task
    
    def add_dependency(self, task_id: str, depends_on: str):
        """
        Add a dependency relationship.
        
        Args:
            task_id: Task that depends on something
            depends_on: Task ID that must complete first
        """
        if task_id not in self.tasks or depends_on not in self.tasks:
            return
        
        self.tasks[task_id].dependencies.add(depends_on)
        
        # Update blocked_by
        if not self.tasks[depends_on].completed:
            self.tasks[task_id].blocked_by.add(depends_on)
        
        self._save()
    
    def mark_completed(self, task_id: str):
        """
        Mark a task as completed and update blocked tasks.
        
        Args:
            task_id: Task ID to mark complete
        """
        if task_id not in self.tasks:
            return
        
        self.tasks[task_id].completed = True
        
        # Unblock dependent tasks
        for task in self.tasks.values():
            if task_id in task.blocked_by:
                task.blocked_by.remove(task_id)
        
        self._save()
    
    def get_topological_order(self) -> List[str]:
        """
        Get tasks in topological order (dependencies first).
        
        Returns:
            List of task IDs in execution order
        
        Raises:
            ValueError: If circular dependency detected
        """
        # Build adjacency list
        in_degree = {task_id: 0 for task_id in self.tasks}
        adj_list = defaultdict(list)
        
        for task_id, task in self.tasks.items():
            if task.completed:
                continue
            
            for dep in task.dependencies:
                if dep in self.tasks and not self.tasks[dep].completed:
                    adj_list[dep].append(task_id)
                    in_degree[task_id] += 1
        
        # Kahn's algorithm
        queue = deque([tid for tid, deg in in_degree.items() if deg == 0 and not self.tasks[tid].completed])
        order = []
        
        while queue:
            current = queue.popleft()
            order.append(current)
            
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        incomplete = [tid for tid, task in self.tasks.items() if not task.completed]
        if len(order) < len(incomplete):
            raise ValueError("Circular dependency detected")
        
        return order
    
    def get_blocked_tasks(self) -> List[Tuple[str, List[str]]]:
        """
        Get tasks that are blocked and what they're blocked by.
        
        Returns:
            List of (task_id, blocking_task_ids) tuples
        """
        blocked = []
        for task_id, task in self.tasks.items():
            if not task.completed and task.blocked_by:
                blockers = list(task.blocked_by)
                blocked.append((task_id, blockers))
        
        return blocked
    
    def get_ready_tasks(self) -> List[str]:
        """
        Get tasks that are ready to execute (no blockers).
        
        Returns:
            List of task IDs ready for execution
        """
        ready = []
        for task_id, task in self.tasks.items():
            if not task.completed and not task.blocked_by:
                ready.append(task_id)
        
        return ready
    
    def infer_dependencies_from_description(self, task_id: str) -> List[str]:
        """
        Attempt to infer dependencies from task description.
        
        Looks for patterns like:
        - "depends on X"
        - "after X"
        - "requires X"
        - "blocked by X"
        
        Args:
            task_id: Task to analyze
        
        Returns:
            List of inferred dependency task IDs
        """
        if task_id not in self.tasks:
            return []
        
        task = self.tasks[task_id]
        text = f"{task.title} {task.description}".lower()
        
        # Patterns that indicate dependencies
        patterns = [
            r'depends?\s+on\s+([a-z0-9_-]+)',
            r'after\s+([a-z0-9_-]+)',
            r'requires?\s+([a-z0-9_-]+)',
            r'blocked\s+by\s+([a-z0-9_-]+)',
            r'needs\s+([a-z0-9_-]+)\s+to\s+be'
        ]
        
        inferred = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Check if match is a known task ID
                if match in self.tasks and match != task_id:
                    inferred.append(match)
        
        return inferred
    
    def to_mermaid(self) -> str:
        """
        Generate Mermaid diagram of dependency graph.
        
        Returns:
            Mermaid markdown syntax
        """
        lines = ["```mermaid", "graph TD"]
        
        # Add nodes
        for task_id, task in self.tasks.items():
            status = "✅" if task.completed else ("🚫" if task.blocked_by else "⚡")
            label = f"{status} {task.title}"
            lines.append(f'    {task_id}["{label}"]')
        
        # Add edges
        for task_id, task in self.tasks.items():
            for dep in task.dependencies:
                lines.append(f'    {dep} --> {task_id}')
        
        lines.append("```")
        return '\n'.join(lines)
    
    def get_stats(self) -> Dict:
        """Get graph statistics."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.completed)
        blocked = sum(1 for t in self.tasks.values() if t.blocked_by and not t.completed)
        ready = sum(1 for t in self.tasks.values() if not t.blocked_by and not t.completed)
        
        return {
            'total_tasks': total,
            'completed': completed,
            'blocked': blocked,
            'ready': ready,
            'graph_file': str(self.graph_file)
        }
    
    def _load(self):
        """Load graph from disk."""
        if not self.graph_file.exists():
            return
        
        try:
            with open(self.graph_file, 'r') as f:
                data = json.load(f)
                self.tasks = {
                    tid: TaskNode.from_dict(tdata)
                    for tid, tdata in data.items()
                }
        except:
            pass
    
    def _save(self):
        """Save graph to disk."""
        try:
            with open(self.graph_file, 'w') as f:
                json.dump(
                    {tid: t.to_dict() for tid, t in self.tasks.items()},
                    f,
                    indent=2
                )
        except:
            pass
