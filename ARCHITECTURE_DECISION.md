# cursor-harness Architecture Decision

## The Problem

**Cursor CLI (`cursor agent run`) has fundamental MCP limitations in headless mode:**
- OAuth-based MCPs fail (Azure DevOps)
- Even non-OAuth MCPs fail (Playwright, Puppeteer)
- MCP approval system designed for GUI, not CLI
- "Connection closed" errors persist despite workarounds

**This is a Cursor architecture issue, not something we can fix.**

---

## The Requirement

**MCP support is ESSENTIAL for cursor-harness because:**
1. E2E testing requires Playwright/Puppeteer MCP
2. Azure DevOps integration requires Azure DevOps MCP
3. Without E2E testing → Ship broken code (AutoGraph proved this!)
4. Without Azure DevOps MCP → No backlog automation

**Without MCP, cursor-harness is useless for real development.**

---

## The Solution: Dual Backend Architecture

**cursor-harness will support TWO backends:**

### **Backend 1: Claude SDK (Recommended)**
```bash
# Set ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY="your-key"

# Run with full MCP support
cursor-harness backlog ~/togglr --project togglr --org X
```

**Features:**
- ✅ Full MCP support (Azure DevOps, Playwright, Puppeteer, etc.)
- ✅ Works in CLI/automation
- ✅ Battle-tested (proven with AutoGraph - 270 iterations!)
- ✅ Perfect for Sherpa microservices
- ❌ Requires Anthropic API key

### **Backend 2: Cursor CLI (Limited)**
```bash
# No API key needed
cursor-harness greenfield ./simple-app --spec specs/simple.txt
```

**Features:**
- ✅ Uses Cursor subscription (no API key)
- ✅ Good for simple projects
- ❌ NO MCP support (Cursor CLI limitation)
- ❌ NO E2E testing
- ❌ NO Azure DevOps integration

---

## Auto-Detection Logic

```python
if os.environ.get("ANTHROPIC_API_KEY"):
    # Use Claude SDK backend (full MCP support)
    from .claude_sdk_client import ClaudeSDKClient
    client = ClaudeSDKClient(...)
else:
    # Use Cursor CLI backend (limited, no MCP)
    from .cursor_cli_client import CursorCLIClient
    client = CursorCLIClient(...)
    print("⚠️  No ANTHROPIC_API_KEY - running without MCP support")
    print("   For MCP tools, set: export ANTHROPIC_API_KEY=...")
```

---

## User Documentation

**For Projects Needing MCP (Recommended):**
```bash
# One-time setup
export ANTHROPIC_API_KEY="sk-ant-..."
# Add to ~/.zshrc to persist

# Then use cursor-harness with full power!
cursor-harness backlog ~/togglr --project togglr --org X
```

**For Simple Projects (No MCP):**
```bash
# No setup needed
cursor-harness greenfield ./simple-app
```

---

## Why This Is Best

1. **User-friendly:** Auto-detects based on API key
2. **Flexible:** Supports both use cases
3. **Honest:** Clearly documents limitations
4. **Pragmatic:** Uses proven tech (Claude SDK) where it works
5. **Future-proof:** If Cursor fixes MCP in CLI, we can use it

---

## Implementation Plan

1. Import Claude SDK dependencies (from autonomous-harness)
2. Add backend detection logic
3. Support both ClaudeSDKClient and CursorCLIClient
4. Update docs to explain both modes
5. Recommend Claude SDK backend for production use

**This gives users CHOICE instead of broken promises!**

