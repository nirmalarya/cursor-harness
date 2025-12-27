# cursor-harness v2.5.0 - Experimental Release

**Released:** December 27, 2025

## Overview

Experimental autonomous coding harness using Cursor CLI with multi-agent workflow.

## Track Record

✅ **Togglr Project:** 29 PBIs completed with quality
- Multi-agent workflow (Architect → Engineer → Tester → CodeReview → Security → DevOps)
- Azure DevOps integration
- ADRs, comprehensive testing, security checks

## Core Capabilities

### 1. Multi-Agent Workflow
- Specialized agents for each phase
- Workflow state management
- Azure DevOps integration

### 2. Backlog Mode
- Processes Azure DevOps PBIs automatically
- Tracks completion state
- Updates work items

### 3. Self-Healing Infrastructure
- Auto-starts Docker services
- Auto-applies database migrations
- Auto-creates MinIO buckets

### 4. Quality Gates
- Loop detection
- Browser cleanup
- Progress tracking

## Architecture

- **Agent:** Cursor CLI (Anthropic-compatible)
- **Workflow:** Multi-agent orchestration
- **State:** workflow-state.json, backlog-state.json
- **MCPs:** Azure DevOps, Playwright

## Known Issues

⚠️ Slow (2-4 hours per PBI)
⚠️ Can get stuck in loops
⚠️ Complex orchestration (10K+ lines)
⚠️ Hard to debug

## Usage

```bash
cursor-harness greenfield ./my-app --spec app_spec.txt
cursor-harness backlog ./project --org MyOrg --project MyProject
cursor-harness enhance ./existing-app
```

## Key Files

- `cursor_harness/cursor_agent_runner.py` - Main orchestrator
- `cursor_harness/multi_agent_mode.py` - Multi-agent workflow
- `cursor_harness/autonomous_backlog_runner.py` - Backlog processing
- `cursor_harness/infrastructure_validator.py` - Self-healing
- `cursor_harness/loop_detector.py` - Loop detection
- `cursor_harness/browser_cleanup.py` - Browser management

## Why This Release?

**Checkpoint before v3.0 rewrite:**
- v2.5.0 is FUNCTIONAL but COMPLEX
- v3.0 will simplify drastically
- This tag preserves multi-agent workflow implementation

## Recommendation

**Use for:** Azure DevOps backlog processing (if patient!)
**Avoid for:** Fast iterations, simple projects

## Lessons Learned

❌ Over-engineered (10K+ lines)
❌ Too many layers of abstraction
❌ Complexity → unreliability

✅ Multi-agent workflow concept is good
✅ Self-healing infrastructure is valuable
✅ Backlog mode is useful

**v3.0 will keep the good parts, simplify the rest!**

---

**This version WORKS but is SLOW. Checkpoint it!** ✅
