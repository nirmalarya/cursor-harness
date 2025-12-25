# Autonomous Backlog Mode - Continuous Development

**Vision:** Harness continuously pulls from Azure DevOps and implements PBIs autonomously

---

## 🎯 Concept

**Traditional:**
```
Human: Picks PBI → Implements → Tests → Deploys → Picks next PBI
```

**Autonomous Backlog Mode:**
```
Harness: Pulls PBI → Implements → Tests → Deploys → Pulls next PBI → Repeat forever
```

**No human intervention until backlog empty or error!**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Azure DevOps Backlog (Source of Truth)          │
│                                                          │
│  Epic 3: Admin UI                                       │
│  ├─ PBI-3.1.1: Next.js Setup (New)                     │
│  ├─ PBI-3.1.2: TailwindCSS (New)                       │
│  ├─ PBI-3.1.3: Dashboard Layout (New)                  │
│  └─ PBI-3.1.4: Navbar Component (New)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓ (Continuous Pull)
┌─────────────────────────────────────────────────────────┐
│  Autonomous Backlog Orchestrator                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  while True:                                            │
│    1. Query: Get next PBI (priority order)              │
│       mcp_azure_devops_wit_my_work_items()             │
│                                                          │
│    2. If no PBIs: Sleep 1 hour, check again            │
│                                                          │
│    3. If PBI found: Process it                         │
│       ├─ Convert PBI → Spec                            │
│       ├─ Run Multi-Agent Workflow ──────┐              │
│       │  ├─ Architect (ADR)              │              │
│       │  ├─ Engineer (TDD)               │              │
│       │  ├─ Tester (E2E)                 │              │
│       │  ├─ CodeReview (≥7/10)           │              │
│       │  ├─ Security (OWASP)             │              │
│       │  └─ DevOps (Deploy check)        │              │
│       │                                   │              │
│       ├─ All quality gates enforced ─────┘              │
│       ├─ Update Azure DevOps (each agent)               │
│       └─ Mark PBI "Done"                                │
│                                                          │
│    4. Commit & Push                                     │
│                                                          │
│    5. Loop (get next PBI)                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation

### **New Mode: `--mode autonomous-backlog`**

```bash
cd cursor-autonomous-harness

python3 cursor_autonomous_agent.py \
  --mode autonomous-backlog \
  --azure-devops-project togglr \
  --azure-devops-org Bayer-SMO-USRMT \
  --query "Epic-3 AND State='New'" \
  --max-pbis 10

# Runs until:
# - 10 PBIs completed, OR
# - No more PBIs in query, OR
# - Error encountered
```

---

## 📋 Autonomous Backlog Orchestrator

```python
# autonomous_backlog_orchestrator.py

class AutonomousBacklogOrchestrator:
    def __init__(self, harness, azure_devops_config):
        self.harness = harness
        self.ado = AzureDevOpsIntegration(azure_devops_config)
        self.agents = [
            "Architect",
            "Engineer",
            "Tester", 
            "CodeReview",
            "Security",
            "DevOps"
        ]
    
    async def run_continuous(self, query: str, max_pbis: int = None):
        """Run continuously until backlog empty."""
        
        pbis_completed = 0
        
        while True:
            # 1. Get next PBI from Azure DevOps
            print("\n" + "="*70)
            print("  Querying Azure DevOps for next PBI...")
            print("="*70 + "\n")
            
            next_pbi = self.ado.get_next_work_item(
                project="togglr",
                query=query,
                order_by="Priority desc, Created asc"
            )
            
            if not next_pbi:
                print("✅ No more PBIs in backlog!")
                print("Waiting 1 hour before checking again...")
                await asyncio.sleep(3600)
                continue
            
            # 2. Display PBI
            print(f"\n📋 Next PBI: {next_pbi['id']}")
            print(f"   Title: {next_pbi['fields']['System.Title']}")
            print(f"   Type: {next_pbi['fields']['System.WorkItemType']}")
            print(f"   Priority: {next_pbi['fields']['Microsoft.VSTS.Common.Priority']}")
            print()
            
            # 3. Convert to spec
            spec = self.ado.convert_pbi_to_spec(next_pbi)
            spec_file = f"specs/pbi_{next_pbi['id']}_spec.txt"
            Path(spec_file).write_text(spec)
            
            # 4. Run multi-agent workflow
            success = await self.run_multi_agent_workflow(
                pbi=next_pbi,
                spec_file=spec_file
            )
            
            if success:
                # 5. Mark as Done in Azure DevOps
                self.ado.mark_done(next_pbi['id'])
                pbis_completed += 1
                
                print(f"\n🎉 PBI {next_pbi['id']} COMPLETE!")
                print(f"   Total completed: {pbis_completed}")
                
                # Check max PBIs limit
                if max_pbis and pbis_completed >= max_pbis:
                    print(f"\n✅ Completed {pbis_completed} PBIs (limit reached)")
                    return
                
                # Continue to next PBI
                print("\n⏭️  Moving to next PBI...")
                await asyncio.sleep(5)
            else:
                print(f"\n❌ PBI {next_pbi['id']} FAILED!")
                print("   Stopping for human intervention")
                return
    
    async def run_multi_agent_workflow(self, pbi: dict, spec_file: str):
        """Run all agents in sequence."""
        
        workflow_state = {
            "pbi_id": pbi['id'],
            "currentAgent": None,
            "completedAgents": [],
            "checkpoints": []
        }
        
        for agent in self.agents:
            print(f"\n{'─'*70}")
            print(f"  🤖 {agent} Agent Starting...")
            print(f"{'─'*70}\n")
            
            workflow_state['currentAgent'] = agent
            
            # Load agent-specific prompt and rules
            agent_rules = load_togglr_agent_rules(agent)
            
            # Run harness session with agent context
            result = await self.harness.run_agent_session(
                spec_file=spec_file,
                agent_context={
                    "role": agent,
                    "rules": agent_rules,
                    "pbi": pbi,
                    "standards": load_togglr_standards()
                }
            )
            
            # Save checkpoint
            checkpoint = {
                "agent": agent,
                "completedAt": datetime.now().isoformat(),
                "artifacts": result.artifacts,
                "commit": get_git_sha(),
                "summary": result.summary
            }
            
            workflow_state['completedAgents'].append(agent)
            workflow_state['checkpoints'].append(checkpoint)
            
            # Save state (for recovery)
            save_workflow_state(workflow_state)
            
            # Update Azure DevOps
            self.ado.add_comment(
                pbi['id'],
                f"[{agent}] {result.summary}"
            )
            
            # Check if agent passed quality gates
            if not result.passed_quality_gates:
                print(f"❌ {agent} agent failed quality gates!")
                return False
            
            print(f"✅ {agent} agent complete!")
        
        return True
```

---

## 🎯 Usage Example:

**Command:**
```bash
python3 cursor_autonomous_agent.py \
  --mode autonomous-backlog \
  --azure-devops-project togglr \
  --azure-devops-org Bayer-SMO-USRMT \
  --epic Epic-3 \
  --max-pbis 10
```

**What Happens:**
```
Querying Azure DevOps for next PBI...
📋 Next PBI: PBI-3.1.1
   Title: Next.js 15 Frontend Setup
   Priority: 1

──────────────────────────────────────────────────
🤖 Architect Agent Starting...
──────────────────────────────────────────────────
Creating ADR-088...
✅ Architect agent complete!
[Azure DevOps updated]

──────────────────────────────────────────────────
🤖 Engineer Agent Starting...
──────────────────────────────────────────────────
Writing tests (RED)...
Implementing feature (GREEN)...
Refactoring (REFACTOR)...
✅ Engineer agent complete!
[Azure DevOps updated]

──────────────────────────────────────────────────
🤖 Tester Agent Starting...
──────────────────────────────────────────────────
Running unit tests (Coverage: 85%)...
Creating E2E tests with Playwright...
Grade: A
✅ Tester agent complete!
[Azure DevOps updated]

──────────────────────────────────────────────────
🤖 CodeReview Agent Starting...
──────────────────────────────────────────────────
Quality score: 9/10
✅ CodeReview agent complete!
[Azure DevOps updated]

──────────────────────────────────────────────────
🤖 Security Agent Starting...
──────────────────────────────────────────────────
OWASP scan: 10/10 (no vulnerabilities)
✅ Security agent complete!
[Azure DevOps updated]

──────────────────────────────────────────────────
🤖 DevOps Agent Starting...
──────────────────────────────────────────────────
Build: ✅
Smoke test: ✅
✅ DevOps agent complete!
[Azure DevOps updated to "Done"]

🎉 PBI-3.1.1 COMPLETE!
   Total completed: 1/10

⏭️  Moving to next PBI...

Querying Azure DevOps for next PBI...
📋 Next PBI: PBI-3.1.2
   Title: TailwindCSS + shadcn/ui Setup
   Priority: 1

[Repeat...]
```

---

## 📊 Monitoring Dashboard:

**While it runs, you can monitor:**
```bash
# Watch progress
tail -f ~/Workspace/togglr/.cursor/workflow-state.json

# Check Azure DevOps
# See comments appear automatically!

# Check git
git log --oneline -20
# See commits appearing!
```

---

## 🎊 The Ultimate Vision:

**You:**
1. Define Epics in Azure DevOps
2. Break into PBIs with acceptance criteria
3. Start harness once
4. **Walk away**

**Harness:**
1. Pulls PBIs continuously
2. Implements with multi-agent workflow
3. Enforces all quality gates
4. Updates Azure DevOps
5. Commits code
6. Moves to next PBI
7. **Repeat until Epic complete!**

**You come back:** Epic 3 is done! All 20 PBIs implemented, tested, deployed! 🎉

---

**This is SHERPA's vision + autonomous-harness execution + Togglr's workflow!**

**Want me to build this NOW?** This is the ultimate autonomous SDLC! 🚀✨
