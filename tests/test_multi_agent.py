"""Tests for multi-agent coordination."""

import tempfile
from pathlib import Path

from cursor_harness.intelligence.multi_agent import (
    MultiAgentCoordinator,
    AgentTask,
    AgentMessage,
    AgentStatus
)


def test_agent_task_creation():
    """Test agent task dataclass."""
    task = AgentTask(
        task_id="task-1",
        agent_id="agent-1",
        description="Test task"
    )
    
    assert task.task_id == "task-1"
    assert task.status == AgentStatus.PENDING.value
    
    # Test serialization
    data = task.to_dict()
    restored = AgentTask.from_dict(data)
    assert restored.task_id == task.task_id


def test_agent_message():
    """Test agent message."""
    msg = AgentMessage(
        message_id="msg-1",
        from_agent="agent-1",
        to_agent="agent-2",
        content={"data": "test"},
        timestamp=1000.0
    )
    
    assert msg.from_agent == "agent-1"
    assert msg.to_agent == "agent-2"


def test_register_agent():
    """Test agent registration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        
        coordinator.register_agent("agent-1", capabilities=["coding"])
        
        assert "agent-1" in coordinator.agents
        assert coordinator.agents["agent-1"]["capabilities"] == ["coding"]


def test_create_task():
    """Test task creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        
        task = coordinator.create_task(
            task_id="task-1",
            description="Build feature",
            agent_id="agent-1"
        )
        
        assert task.task_id == "task-1"
        assert task.agent_id == "agent-1"
        assert task.status == AgentStatus.PENDING.value


def test_task_lifecycle():
    """Test task status transitions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        
        task = coordinator.create_task("task-1", "Test", agent_id="agent-1")
        
        # Start task
        coordinator.start_task("task-1")
        assert coordinator.tasks["task-1"].status == AgentStatus.RUNNING.value
        
        # Complete task
        coordinator.complete_task("task-1", result={"output": "success"})
        assert coordinator.tasks["task-1"].status == AgentStatus.COMPLETED.value
        assert coordinator.tasks["task-1"].result == {"output": "success"}


def test_task_failure():
    """Test task failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        
        task = coordinator.create_task("task-1", "Test", agent_id="agent-1")
        coordinator.start_task("task-1")
        coordinator.fail_task("task-1", error="Something went wrong")
        
        assert coordinator.tasks["task-1"].status == AgentStatus.FAILED.value
        assert coordinator.tasks["task-1"].error == "Something went wrong"


def test_task_dependencies():
    """Test task dependency resolution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        
        # Create tasks with dependencies
        task1 = coordinator.create_task("task-1", "Base", agent_id="agent-1")
        task2 = coordinator.create_task(
            "task-2",
            "Depends on task-1",
            agent_id="agent-1",
            dependencies=["task-1"]
        )
        
        # task-2 should not be ready (task-1 pending)
        ready = coordinator.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "task-1"
        
        # Complete task-1
        coordinator.start_task("task-1")
        coordinator.complete_task("task-1", result="done")
        
        # Now task-2 should be ready
        ready = coordinator.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "task-2"


def test_message_passing():
    """Test agent message passing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        coordinator.register_agent("agent-2")
        
        # Send message
        msg = coordinator.send_message(
            from_agent="agent-1",
            to_agent="agent-2",
            content="Hello agent-2"
        )
        
        assert msg.from_agent == "agent-1"
        assert msg.to_agent == "agent-2"
        
        # Get messages for agent-2
        messages = coordinator.get_messages_for_agent("agent-2")
        assert len(messages) == 1
        assert messages[0].content == "Hello agent-2"


def test_get_tasks_for_agent():
    """Test getting tasks for specific agent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        coordinator.register_agent("agent-2")
        
        coordinator.create_task("task-1", "For agent-1", agent_id="agent-1")
        coordinator.create_task("task-2", "For agent-2", agent_id="agent-2")
        coordinator.create_task("task-3", "Also for agent-1", agent_id="agent-1")
        
        agent1_tasks = coordinator.get_tasks_for_agent("agent-1")
        assert len(agent1_tasks) == 2
        
        agent2_tasks = coordinator.get_tasks_for_agent("agent-2")
        assert len(agent2_tasks) == 1


def test_get_task_results():
    """Test getting completed task results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        
        coordinator.create_task("task-1", "Test 1", agent_id="agent-1")
        coordinator.create_task("task-2", "Test 2", agent_id="agent-1")
        
        coordinator.start_task("task-1")
        coordinator.complete_task("task-1", result="Result 1")
        
        coordinator.start_task("task-2")
        coordinator.complete_task("task-2", result="Result 2")
        
        results = coordinator.get_task_results()
        assert len(results) == 2
        assert results["task-1"] == "Result 1"
        assert results["task-2"] == "Result 2"


def test_get_status():
    """Test coordinator status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coordinator = MultiAgentCoordinator(Path(tmpdir))
        coordinator.register_agent("agent-1")
        coordinator.register_agent("agent-2")
        
        coordinator.create_task("task-1", "Test", agent_id="agent-1")
        coordinator.send_message("agent-1", "agent-2", "test")
        
        status = coordinator.get_status()
        
        assert status['total_agents'] == 2
        assert status['total_tasks'] == 1
        assert status['total_messages'] == 1


def test_persistence():
    """Test coordinator state persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        coordinator_id = "test-coord"
        
        # Create coordinator and tasks
        coord1 = MultiAgentCoordinator(project_dir, coordinator_id=coordinator_id)
        coord1.register_agent("agent-1")
        coord1.create_task("task-1", "Test", agent_id="agent-1")
        coord1.send_message("agent-1", "agent-2", "test message")
        
        # Create new instance (simulating restart)
        coord2 = MultiAgentCoordinator(project_dir, coordinator_id=coordinator_id)
        
        # Should load persisted state
        assert len(coord2.tasks) == 1
        assert "task-1" in coord2.tasks
        assert len(coord2.messages) == 1


if __name__ == '__main__':
    test_agent_task_creation()
    test_agent_message()
    test_register_agent()
    test_create_task()
    test_task_lifecycle()
    test_task_failure()
    test_task_dependencies()
    test_message_passing()
    test_get_tasks_for_agent()
    test_get_task_results()
    test_get_status()
    test_persistence()
    print("✅ All multi-agent tests passed!")
