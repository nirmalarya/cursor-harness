# Quality Gate #12: Smoke Test Suite (At 100% Completion)

**Final verification - test critical user flows work end-to-end**

---

## 🚨 THE PROBLEM (From AutoGraph v3.1)

**What happened:**
```
Agent reached 666/666 features (100%)
Agent claimed everything works
But:
- Save diagram still broken in browser
- Create folder unreliable
- Never tested complete user flows
```

**Agent marked 100% without final verification!**

---

## ✅ THE SOLUTION - Mandatory Smoke Test

### When: At 100% Feature Completion

```bash
# This runs when all features are marked passing

total=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
passing=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len([f for f in json.load(sys.stdin) if f.get('passes')]))")

if [ "$passing" = "$total" ]; then
    echo "🎉 All $total features marked as passing!"
    echo ""
    echo "🔥 RUNNING FINAL SMOKE TEST SUITE..."
    echo "Testing critical user flows end-to-end"
    echo ""
    
    # Run smoke tests (MANDATORY!)
    # Do NOT exit/complete without smoke test passing!
fi
```

---

## 🧪 Generic Smoke Test Strategy

**Test the 5-10 most critical user flows:**

### For Web Applications:

```markdown
## Critical Flows (adapt to your app):

1. **Authentication Flow**
   - Register new user
   - Login
   - Access protected page
   - Logout
   
2. **Core CRUD Flow**
   - Create primary resource
   - Read/view resource
   - Update resource
   - Delete resource
   - Verify persists across reload
   
3. **Primary User Journey**
   - Complete the #1 use case
   - The reason users use your app
   - End-to-end, realistic scenario

Example Smoke Test Script (web app):
```bash
#!/bin/bash
# smoke_test.sh - Critical flows

echo "=== SMOKE TEST SUITE ==="

# 1. Check app accessible
curl -f http://localhost:${FRONTEND_PORT:-3000} >/dev/null 2>&1 || {
    echo "❌ Frontend not accessible"
    exit 1
}

# 2. Check API accessible
curl -f http://localhost:${API_PORT:-8080}/health >/dev/null 2>&1 || {
    echo "❌ API not accessible"
    exit 1
}

# 3. Test authentication (if app has auth)
response=$(curl -s -X POST http://localhost:${API_PORT:-8080}/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"smoke-test@example.com\",\"password\":\"Test123!\"}")

echo "$response" | grep -q "id\|user\|success" || {
    echo "❌ Registration failed"
    exit 1
}

# 4. Test core CRUD (adapt to your app's main resource)
# Create
# Read
# Update
# Delete

echo "✅ All smoke tests passed!"
```

---

### For APIs:

```markdown
## Critical Endpoints (test top 3-5):

1. Health check endpoint
2. Authentication endpoint
3. Primary resource CRUD
4. Most used endpoint
5. Most complex endpoint

Example:
```bash
# 1. Health
curl -f http://localhost:8000/health

# 2. Auth
curl -X POST http://localhost:8000/auth/login -d '{"user":"test","pass":"test"}'

# 3. Main resource
curl -X POST http://localhost:8000/api/resource -d '{"data":"test"}'
curl -X GET http://localhost:8000/api/resource/1
curl -X PUT http://localhost:8000/api/resource/1 -d '{"data":"updated"}'
curl -X DELETE http://localhost:8000/api/resource/1
```

---

### For CLI Tools:

```markdown
## Critical Commands (test main workflows):

1. `--help` works
2. Main command works
3. Data persists
4. Config works

Example:
```bash
# 1. Help
./cli-tool --help | grep -q "Usage"

# 2. Main command
./cli-tool create --name "smoke-test"

# 3. List/show
./cli-tool list | grep -q "smoke-test"

# 4. Update
./cli-tool update "smoke-test" --name "updated"

# 5. Verify
./cli-tool list | grep -q "updated"
```

---

## 🎯 Smoke Test Requirements (Generic)

**Before claiming project complete, verify:**

### 1. Application Starts
```bash
# For web apps
curl -f http://localhost:PORT

# For APIs
curl -f http://localhost:PORT/health

# For CLIs
./cli-tool --version

# For services
docker-compose ps | grep -c "healthy"
```

### 2. Authentication Works (if applicable)
```bash
# Register/login/access protected resource
# Use actual endpoints, not mocks
```

### 3. Core Functionality Works
```bash
# Test the PRIMARY use case
# The #1 reason people use your app
# Complete workflow, not isolated actions
```

### 4. Data Persists
```bash
# Create data
# Restart app/reload page
# Verify data still there
```

### 5. No Critical Errors
```bash
# Check logs (no ERROR level)
# Check console (no red errors)
# Check API responses (no 500s)
```

---

## 📋 Integration into Prompt

**Add to coding_prompt.md (when reaching 100%):**

```markdown
### WHEN 100% COMPLETE: RUN SMOKE TEST SUITE

**MANDATORY: Final verification before claiming done!**

```bash
total=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
passing=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len([f for f in json.load(sys.stdin) if f.get('passes')]))")

if [ "$passing" = "$total" ]; then
    echo "🎉 All $total features marked passing!"
    echo ""
    echo "🔥 RUNNING FINAL SMOKE TEST..."
    echo ""
    
    # Create and run smoke test
    cat > smoke_test.sh << 'SMOKE_EOF'
#!/bin/bash
set -e

echo "=== SMOKE TEST SUITE ==="

# 1. App accessible
echo "1. Testing application accessibility..."
# [Adapt to your project type]

# 2. Authentication
echo "2. Testing authentication..."
# [If applicable]

# 3. Core functionality
echo "3. Testing core user flow..."
# [Most important workflow]

# 4. Data persistence
echo "4. Testing data persistence..."
# [Create, reload, verify]

echo ""
echo "✅ ALL SMOKE TESTS PASSED!"
echo "Project is production-ready!"
SMOKE_EOF
    
    chmod +x smoke_test.sh
    ./smoke_test.sh
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ SMOKE TESTS PASSED - PROJECT COMPLETE!"
        echo "Update progress and exit."
        exit 0
    else
        echo ""
        echo "❌ SMOKE TESTS FAILED!"
        echo "Fix issues before claiming 100% complete!"
        exit 1
    fi
fi
```

**DO NOT claim 100% complete without smoke tests passing!**
```

---

## ✅ What Makes This Generic

**Instead of:**
```
❌ "Test AutoGraph login → create diagram → save"
❌ "Verify MinIO bucket has files"
❌ "Check PostgreSQL tables populated"
```

**We say:**
```
✅ "Test authentication flow"
✅ "Test core CRUD operations"
✅ "Verify data storage works"
✅ "Check primary use case works"
```

**Agent adapts to the specific project!**

---

**Smoke test framework defined! Ready to integrate?** 🎯

