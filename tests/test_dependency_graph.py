"""Tests for dependency graph."""

import tempfile
from pathlib import Path

from cursor_harness.intelligence.dependency_graph import DependencyGraph, TaskNode


def test_add_task():
    """Test adding tasks to graph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = DependencyGraph(Path(tmpdir))
        
        task = graph.add_task(
            task_id="feature-1",
            title="Implement authentication",
            description="Add user login system"
        )
        
        assert task.task_id == "feature-1"
        assert task.title == "Implement authentication"
        assert not task.completed
        assert len(task.dependencies) == 0


def test_dependencies():
    """Test dependency relationships."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = DependencyGraph(Path(tmpdir))
        
        # Add tasks
        graph.add_task("base", "Base system", "Core functionality")
        graph.add_task("auth", "Authentication", "Login system", dependencies=["base"])
        graph.add_task("api", "API", "REST API", dependencies=["base", "auth"])
        
        # Check dependencies
        assert "base" in graph.tasks["auth"].dependencies
        assert "base" in graph.tasks["api"].dependencies
        assert "auth" in graph.tasks["api"].dependencies
        
        # Check blocked_by
        assert "base" in graph.tasks["auth"].blocked_by
        assert "base" in graph.tasks["api"].blocked_by
        assert "auth" in graph.tasks["api"].blocked_by


def test_topological_order():
    """Test topological sorting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = DependencyGraph(Path(tmpdir))
        
        graph.add_task("a", "Task A", "First")
        graph.add_task("b", "Task B", "Second", dependencies=["a"])
        graph.add_task("c", "Task C", "Third", dependencies=["a", "b"])
        
        order = graph.get_topological_order()
        
        # 'a' must come before 'b' and 'c'
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        # 'b' must come before 'c'
        assert order.index("b") < order.index("c")


def test_mark_completed():
    """Test marking tasks complete and unblocking dependents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = DependencyGraph(Path(tmpdir))
        
        graph.add_task("base", "Base", "Foundation")
        graph.add_task("feature", "Feature", "Depends on base", dependencies=["base"])
        
        # Feature should be blocked
        assert "base" in graph.tasks["feature"].blocked_by
        
        # Complete base
        graph.mark_completed("base")
        
        # Feature should be unblocked
        assert len(graph.tasks["feature"].blocked_by) == 0
        assert graph.tasks["base"].completed


def test_get_ready_tasks():
    """Test finding ready tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = DependencyGraph(Path(tmpdir))
        
        graph.add_task("a", "A", "No deps")
        graph.add_task("b", "B", "No deps")
        graph.add_task("c", "C", "Depends on A", dependencies=["a"])
        
        ready = graph.get_ready_tasks()
        
        # A and B are ready (no dependencies)
        assert "a" in ready
        assert "b" in ready
        # C is blocked
        assert "c" not in ready


def test_get_blocked_tasks():
    """Test finding blocked tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = DependencyGraph(Path(tmpdir))
        
        graph.add_task("base", "Base", "Foundation")
        graph.add_task("feature1", "Feature 1", "Blocked", dependencies=["base"])
        graph.add_task("feature2", "Feature 2", "Also blocked", dependencies=["base", "feature1"])
        
        blocked = graph.get_blocked_tasks()
        
        # Should have 2 blocked tasks
        assert len(blocked) == 2
        
        # feature1 blocked by base
        feature1_block = next(t for t in blocked if t[0] == "feature1")
        assert "base" in feature1_block[1]
        
        # feature2 blocked by base and feature1
        feature2_block = next(t for t in blocked if t[0] == "feature2")
        assert "base" in feature2_block[1]
        assert "feature1" in feature2_block[1]


def test_mermaid_output():
    """Test Mermaid diagram generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = DependencyGraph(Path(tmpdir))
        
        graph.add_task("a", "Task A", "First")
        graph.add_task("b", "Task B", "Second", dependencies=["a"])
        
        mermaid = graph.to_mermaid()
        
        assert "```mermaid" in mermaid
        assert "graph TD" in mermaid
        assert "a -->" in mermaid or "a --> b" in mermaid
        assert "Task A" in mermaid
        assert "Task B" in mermaid


def test_persistence():
    """Test graph persists across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create graph and add tasks
        graph1 = DependencyGraph(project_dir)
        graph1.add_task("task1", "Task 1", "Description")
        graph1.add_task("task2", "Task 2", "Description", dependencies=["task1"])
        
        # Create new graph instance (simulating restart)
        graph2 = DependencyGraph(project_dir)
        
        # Should load persisted tasks
        assert len(graph2.tasks) == 2
        assert "task1" in graph2.tasks
        assert "task2" in graph2.tasks
        assert "task1" in graph2.tasks["task2"].dependencies


if __name__ == '__main__':
    test_add_task()
    test_dependencies()
    test_topological_order()
    test_mark_completed()
    test_get_ready_tasks()
    test_get_blocked_tasks()
    test_mermaid_output()
    test_persistence()
    print("✅ All dependency graph tests passed!")
