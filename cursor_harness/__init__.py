"""
cursor-harness - Autonomous Coding Harness
===========================================

Enterprise-grade autonomous coding with multi-agent workflow and Azure DevOps integration.
"""

__version__ = "2.3.0-dev"

from .cursor_agent_runner import run_autonomous_agent
from .autonomous_backlog_runner import run_autonomous_backlog
from .multi_agent_mode import MultiAgentWorkflow
from .azure_devops_integration import AzureDevOpsIntegration

__all__ = [
    "run_autonomous_agent",
    "run_autonomous_backlog",
    "MultiAgentWorkflow",
    "AzureDevOpsIntegration",
]

