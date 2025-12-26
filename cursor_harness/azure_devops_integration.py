#!/usr/bin/env python3
"""
Azure DevOps Integration for cursor-harness
============================================

Integrates with Azure DevOps via REST API (reliable for CLI automation).
"""

from typing import Dict, List, Optional
import os
import requests
import json


class AzureDevOpsIntegration:
    """Azure DevOps integration via Cursor MCP."""
    
    def __init__(self, organization: str, project: str):
        self.organization = organization
        self.project = project
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        
        # Get PAT token from environment
        self.pat = os.environ.get("AZURE_DEVOPS_PAT")
        if not self.pat:
            print("⚠️  AZURE_DEVOPS_PAT not set - Azure DevOps queries will fail")
            print("   Generate PAT: https://dev.azure.com/{org}/_usersSettings/tokens")
            print("   Then: export AZURE_DEVOPS_PAT='your-pat-here'")
        
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.pat:
            # PAT token uses basic auth with empty username
            import base64
            auth = base64.b64encode(f":{self.pat}".encode()).decode()
            self.headers["Authorization"] = f"Basic {auth}"
    
    def get_work_item(self, work_item_id: int) -> Optional[Dict]:
        """
        Fetch work item from Azure DevOps via REST API.
        
        Args:
            work_item_id: Numeric work item ID
        
        Returns:
            Work item details or None if error
        """
        if not self.pat:
            print(f"❌ Cannot fetch work item {work_item_id} - no PAT token")
            return None
        
        url = f"{self.base_url}/wit/workitems/{work_item_id}?$expand=relations&api-version=7.1"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch work item {work_item_id}: {e}")
            return None
    
    def query_work_items(
        self,
        query: str = None,
        epic: str = None,
        state: str = "New",
        work_item_type: str = "Product Backlog Item",
        order_by: str = "Priority",
        top: int = 10
    ) -> List[int]:
        """
        Query work items from Azure DevOps via REST API.
        
        Returns list of work item IDs matching criteria.
        """
        if not self.pat:
            print("❌ Cannot query work items - no PAT token")
            return []
        
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
        
        # Execute WIQL query via REST API
        url = f"{self.base_url}/wit/wiql?api-version=7.1"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={"query": wiql},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract work item IDs
            work_items = result.get("workItems", [])
            ids = [item["id"] for item in work_items[:top]]
            
            print(f"📋 Found {len(ids)} work items matching criteria")
            return ids
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to query work items: {e}")
            return []
    
    def add_comment(self, work_item_id: int, comment: str):
        """Add comment to work item via REST API."""
        if not self.pat:
            print(f"⚠️  Cannot add comment to {work_item_id} - no PAT token")
            return
        
        url = f"{self.base_url}/wit/workitems/{work_item_id}/comments?api-version=7.1-preview.3"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={"text": comment},
                timeout=10
            )
            response.raise_for_status()
            print(f"✅ Added comment to work item {work_item_id}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to add comment: {e}")
    
    def update_work_item(self, work_item_id: int, field: str, value: str):
        """Update work item field via REST API."""
        if not self.pat:
            print(f"⚠️  Cannot update {work_item_id} - no PAT token")
            return
        
        url = f"{self.base_url}/wit/workitems/{work_item_id}?api-version=7.1"
        
        try:
            response = requests.patch(
                url,
                headers={"Content-Type": "application/json-patch+json", **self.headers},
                json=[{
                    "op": "add",
                    "path": f"/fields/{field}",
                    "value": value
                }],
                timeout=10
            )
            response.raise_for_status()
            print(f"✅ Updated work item {work_item_id}: {field} = {value}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to update work item: {e}")
    
    def mark_done(self, work_item_id: int):
        """Mark work item as Done."""
        self.update_work_item(work_item_id, "System.State", "Done")
    
    def get_next_new_pbi(self, epic: Optional[str] = None) -> Optional[int]:
        """
        Get the next 'New' PBI from backlog.
        
        Args:
            epic: Optional epic filter (e.g., "Epic-3")
        
        Returns:
            Work item ID or None if no PBIs found
        """
        ids = self.query_work_items(epic=epic, state="New", top=1)
        return ids[0] if ids else None
    
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

