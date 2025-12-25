# Generic E2E Testing Requirements

**These apply to ANY project (web, mobile, API, CLI, desktop)**

---

## 🎯 Core Principle

**Test complete user workflows, not implementation details.**

The E2E test should:
- ✅ Test from user's perspective
- ✅ Verify end-to-end flow works
- ✅ Use the ACTUAL interface (browser/CLI/app)
- ✅ Verify data persists correctly
- ❌ NOT test internal implementation
- ❌ NOT assume infrastructure works
- ❌ NOT test in isolation

---

## 📋 Generic E2E Testing Framework

### Step 1: Identify Project Type

```bash
# Detect project type automatically
if [ -f "package.json" ] && grep -q "next\|react\|vue" package.json; then
    PROJECT_TYPE="web-frontend"
elif [ -f "requirements.txt" ] && grep -q "fastapi\|django\|flask" requirements.txt; then
    PROJECT_TYPE="web-backend"
elif [ -f "package.json" ] && grep -q "electron" package.json; then
    PROJECT_TYPE="desktop"
elif [ -f "setup.py" ] || grep -q "click\|typer" requirements.txt; then
    PROJECT_TYPE="cli"
else
    PROJECT_TYPE="unknown"
fi

echo "Detected project type: $PROJECT_TYPE"
```

---

## 🌐 Web Application E2E (Puppeteer/Playwright)

**For web apps with frontend:**

### Template: Test Complete User Flow

```markdown
Test: [Feature Name] - Complete User Flow

1. Start from logged-out state
2. Perform authentication (if needed)
3. Navigate to feature
4. Perform action
5. Verify immediate feedback
6. Verify data persistence (reload/revisit)
7. Verify no errors in console

Example (Generic - adapt to your app):
1. Navigate to http://localhost:[PORT]
2. Login/authenticate
3. Perform create/update/delete action
4. Verify success message shown
5. Refresh page or navigate away and back
6. Verify data still there
7. Check browser console (zero errors)
```

**Tools:** Puppeteer MCP (use existing tools)

```python
# Generic E2E template
mcp__puppeteer__puppeteer_navigate(url="http://localhost:PORT/feature")
mcp__puppeteer__puppeteer_screenshot(name="before")
# Perform action (adapt to your UI)
mcp__puppeteer__puppeteer_click(element="button", ref="[data-testid=action]")
# Verify success
mcp__puppeteer__puppeteer_wait_for(text="Success")
# Verify persistence
mcp__puppeteer__puppeteer_navigate(url="http://localhost:PORT/feature")
mcp__puppeteer__puppeteer_screenshot(name="after-reload")
# Check for expected content
```

---

## 🔌 API/Backend E2E

**For APIs and backend services:**

### Template: Test Complete API Flow

```bash
# Generic API testing (adapt URLs and data)

# 1. Test endpoint exists
curl -s http://localhost:PORT/health || echo "Service not running"

# 2. Test create/update flow
response=$(curl -s -X POST http://localhost:PORT/resource \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}')

# 3. Verify response
echo "$response" | grep -q "id" || echo "❌ Create failed"

# 4. Extract ID (adapt to your response format)
id=$(echo "$response" | jq -r '.id' 2>/dev/null || echo "unknown")

# 5. Verify data persists (read it back)
curl -s http://localhost:PORT/resource/$id | grep -q "data" || echo "❌ Not persisted"

# 6. Test update
curl -s -X PUT http://localhost:PORT/resource/$id \
  -H "Content-Type: application/json" \
  -d '{"test": "updated"}' | grep -q "updated" || echo "❌ Update failed"

# 7. Verify update persisted
curl -s http://localhost:PORT/resource/$id | grep -q "updated" || echo "❌ Update not persisted"
```

---

## 💻 CLI Application E2E

**For command-line tools:**

### Template: Test CLI Flow

```bash
# Generic CLI testing

# 1. Test command exists
./cli-tool --help || echo "❌ CLI not executable"

# 2. Test basic command
output=$(./cli-tool create --name "test")

# 3. Verify output
echo "$output" | grep -q "created" || echo "❌ Create failed"

# 4. Test data persists (if CLI uses storage)
./cli-tool list | grep -q "test" || echo "❌ Not persisted"

# 5. Test update
./cli-tool update "test" --name "updated"

# 6. Verify update
./cli-tool list | grep -q "updated" || echo "❌ Update not persisted"
```

---

## 📱 Generic E2E Checklist (Project-Agnostic)

**Before marking ANY feature as passing:**

- [ ] **Authentication works** (if app has auth)
  - Can login/register
  - Tokens/sessions work
  - Protected routes actually protected

- [ ] **Data persistence verified**
  - Create → Data saved
  - Read → Data retrieved correctly
  - Update → Changes persist
  - Delete → Data removed
  - Reload/restart → Data still there

- [ ] **Error handling works**
  - Invalid input rejected gracefully
  - Error messages shown
  - No crashes or 500 errors
  - User can recover from errors

- [ ] **User interface works** (if applicable)
  - Page/screen loads
  - Buttons clickable
  - Forms submittable
  - Visual feedback shown
  - No console errors

- [ ] **Integration verified**
  - Frontend → Backend communication works
  - API calls succeed
  - WebSocket connections (if applicable)
  - External services work (if applicable)

---

## ⚠️ What NOT to Test (Too Specific)

**DON'T include in generic prompts:**
- ❌ "Check MinIO buckets exist"
- ❌ "Verify PostgreSQL schema"
- ❌ "Test FastAPI endpoints"
- ❌ "Check Next.js build"
- ❌ "Verify Docker containers healthy"

**DO include instead:**
- ✅ "Verify data storage works"
- ✅ "Test backend responds"
- ✅ "Ensure frontend accessible"
- ✅ "Check build succeeds"
- ✅ "Verify services running"

**The agent adapts the generic requirement to the specific project!**

---

## 🎯 How Agent Uses This

**Agent reads spec** → Detects it's a web app with FastAPI + Next.js

**Agent applies generic requirement:**
```
"Verify data storage works"
```

**Agent adapts to project:**
```bash
# For AutoGraph (web app), agent does:
- Check Postgres database
- Check MinIO buckets
- Verify data in both

# For CLI tool, agent would do:
- Check file system
- Check config file
- Verify data in files

# For mobile app, agent would do:
- Check local database (SQLite)
- Check remote API
- Verify data synced
```

**Generic requirement → Project-specific implementation!**

---

## ✅ This is Truly Generic!

Works for:
- Web apps (AutoGraph, SHERPA dashboard)
- APIs (REST, GraphQL, gRPC)
- CLI tools (SHERPA CLI)
- Desktop apps (Electron, Tauri)
- Mobile apps (React Native, Flutter)

**The PATTERN is generic, the IMPLEMENTATION adapts!**

