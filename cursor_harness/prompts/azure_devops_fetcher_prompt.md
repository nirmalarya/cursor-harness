# Azure DevOps Work Item Fetcher

**Your role:** Fetch and convert Azure DevOps work item to specification format

---

## TASK

You are given a work item ID. Fetch it from Azure DevOps and create a specification file.

**Work Item ID:** {{WORK_ITEM_ID}}
**Project:** {{PROJECT_NAME}}
**Organization:** {{ORGANIZATION}}

---

## STEP 1: Fetch Work Item from Azure DevOps

Use the Azure DevOps MCP tool to fetch the work item:

```
Use mcp_azure-devops_wit_get_work_item to fetch work item {{WORK_ITEM_ID}}

Parameters:
- id: {{WORK_ITEM_ID}}
- project: {{PROJECT_NAME}}
- expand: "relations"
```

This will return the complete work item with:
- Title
- Description
- Acceptance Criteria
- Tags (Epic)
- Priority
- Current State
- Relations (parent/children)

---

## STEP 2: Extract Key Information

From the work item, extract:

1. **ID:** System.Id
2. **Title:** System.Title
3. **Type:** System.WorkItemType (PBI, Bug, Feature)
4. **Description:** System.Description
5. **Acceptance Criteria:** Microsoft.VSTS.Common.AcceptanceCriteria
6. **Tags/Epic:** System.Tags
7. **Priority:** Microsoft.VSTS.Common.Priority

---

## STEP 3: Create Specification File

Write the extracted information to `spec/{{WORK_ITEM_ID}}_spec.txt`:

```xml
<work_item_specification>
  <azure_devops>
    <organization>{{ORGANIZATION}}</organization>
    <project>{{PROJECT_NAME}}</project>
    <id>{{WORK_ITEM_ID}}</id>
    <url>https://dev.azure.com/{{ORGANIZATION}}/{{PROJECT_NAME}}/_workitems/edit/{{WORK_ITEM_ID}}</url>
  </azure_devops>
  
  <work_item>
    <type>[PBI/Bug/Feature]</type>
    <title>[Title from Azure DevOps]</title>
    <epic>[Epic tag if present]</epic>
    <priority>[1-4]</priority>
  </work_item>
  
  <description>
[Paste System.Description here]
  </description>
  
  <acceptance_criteria>
[Paste Microsoft.VSTS.Common.AcceptanceCriteria here]
  </acceptance_criteria>
  
  <quality_requirements>
    <architect>Create ADR documenting technical approach</architect>
    <engineer>Implement with TDD (tests first!), ≥80% coverage</engineer>
    <tester>E2E tests with Playwright MCP, Grade ≥B</tester>
    <code_review>Quality score ≥7/10</code_review>
    <security>OWASP Top 10 review, ≥7/10, no critical vulnerabilities</security>
    <devops>Build verification, E2E smoke test, deployment ready</devops>
  </quality_requirements>
</work_item_specification>
```

---

## STEP 4: Commit the Spec

```bash
git add spec/{{WORK_ITEM_ID}}_spec.txt
git commit -m "spec: Add specification for {{WORK_ITEM_ID}}

Fetched from Azure DevOps
Ready for multi-agent workflow"
```

---

## STEP 5: Output Summary

Print a summary:

```
✅ Work Item Fetched: {{WORK_ITEM_ID}}
✅ Specification Created: spec/{{WORK_ITEM_ID}}_spec.txt
✅ Ready for multi-agent workflow

Next: Run agents (Architect → Engineer → Tester → CodeReview → Security → DevOps)
```

---

**Your task is COMPLETE when spec file is created and committed.**

Do NOT implement the feature - just fetch and create spec!

