#!/usr/bin/env python3
"""
Azure DevOps Integration for cursor-autonomous-harness
======================================================

Integrates with Azure DevOps via Cursor's MCP support.
"""

from typing import Dict, List, Optional
import subprocess
import json


class AzureDevOpsIntegration:
    """Azure DevOps integration via Cursor MCP."""
    
    def __init__(self, organization: str, project: str):
        self.organization = organization
        self.project = project
    
    def get_work_item(self, work_item_id: str) -> Optional[Dict]:
        """
        Fetch work item from Azure DevOps.
        
        Uses Cursor's MCP Azure DevOps integration.
        For now, this is a placeholder - would use actual MCP call.
        """
        
        # TODO: Implement actual MCP call via Cursor
        # This would be something like:
        # result = cursor_mcp_call("azure-devops", "get_work_item", {
        #     "id": work_item_id,
        #     "project": self.project,
        #     "expand": "relations"
        # })
        
        # Placeholder - return mock data
        return {
            "id": work_item_id,
            "fields": {
                "System.Title": "Example PBI Title",
                "System.Description": "Example description",
                "System.WorkItemType": "Product Backlog Item",
                "Microsoft.VSTS.Common.AcceptanceCriteria": "Example acceptance criteria",
                "System.Tags": "Epic-3",
                "Microsoft.VSTS.Common.Priority": 1
            }
        }
    
    def query_work_items(
        self,
        query: str = None,
        epic: str = None,
        state: str = "New",
        work_item_type: str = "Product Backlog Item",
        order_by: str = "Priority",
        top: int = 1
    ) -> List[Dict]:
        """
        Query work items from Azure DevOps.
        
        Returns list of work items matching criteria.
        """
        
        # Build WIQL query
        if query:
            wiql = query
        elif epic:
            wiql = f"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.TeamProject] = '{self.project}'
              AND [System.WorkItemType] = '{work_item_type}'
              AND [System.Tags] CONTAINS '{epic}'
              AND [System.State] = '{state}'
            ORDER BY [Microsoft.VSTS.Common.{order_by}] DESC
            """
        else:
            wiql = f"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.TeamProject] = '{self.project}'
              AND [System.WorkItemType] = '{work_item_type}'
              AND [System.State] = '{state}'
            ORDER BY [Microsoft.VSTS.Common.{order_by}] DESC
            """
        
        # TODO: Execute query via MCP
        # results = cursor_mcp_call("azure-devops", "query_work_items", {...})
        
        # Placeholder
        return []
    
    def add_comment(self, work_item_id: str, comment: str):
        """Add comment to work item."""
        
        # TODO: Implement via MCP
        # cursor_mcp_call("azure-devops", "add_work_item_comment", {
        #     "project": self.project,
        #     "workItemId": work_item_id,
        #     "comment": comment
        # })
        
        print(f"Would add comment to {work_item_id}: {comment[:50]}...")
    
    def update_work_item(self, work_item_id: str, field: str, value: str):
        """Update work item field."""
        
        # TODO: Implement via MCP
        # cursor_mcp_call("azure-devops", "update_work_item", {
        #     "id": work_item_id,
        #     "updates": [{"path": f"/fields/{field}", "value": value}]
        # })
        
        print(f"Would update {work_item_id}: {field} = {value}")
    
    def mark_done(self, work_item_id: str):
        """Mark work item as Done."""
        self.update_work_item(work_item_id, "System.State", "Done")
    
    def convert_to_spec(self, work_item: Dict) -> str:
        """Convert Azure DevOps work item to harness spec format."""
        
        spec = f"""<work_item_specification>
  <id>{work_item['id']}</id>
  <type>{work_item['fields']['System.WorkItemType']}</type>
  <title>{work_item['fields']['System.Title']}</title>
  
  <description>
{work_item['fields'].get('System.Description', 'No description')}
  </description>
  
  <acceptance_criteria>
{work_item['fields'].get('Microsoft.VSTS.Common.AcceptanceCriteria', 'No acceptance criteria')}
  </acceptance_criteria>
  
  <tags>{work_item['fields'].get('System.Tags', '')}</tags>
  <priority>{work_item['fields'].get('Microsoft.VSTS.Common.Priority', 2)}</priority>
  
  <quality_requirements>
    <architect>Create ADR with technical design</architect>
    <engineer>Implement with TDD (≥80% coverage)</engineer>
    <tester>E2E tests + Grade ≥B</tester>
    <code_review>Quality score ≥7/10</code_review>
    <security>OWASP scan ≥7/10, no critical vulnerabilities</security>
    <devops>Build passes, smoke test passes, deployment ready</devops>
  </quality_requirements>
</work_item_specification>
"""
        return spec

