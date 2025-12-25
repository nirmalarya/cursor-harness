# Quality Gates - MANDATORY Checks Before Marking Features as Passing

**These gates prevent the issues found in AutoGraph v3.0!**

---

## 🛑 GATE 1: STOP CONDITION CHECK (FIRST!)

**BEFORE doing ANY work, check if project is complete:**

```bash
#!/bin/bash
# Check completion status

total=$(cat feature_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
passing=$(cat feature_list.json | python3 -c "import json, sys; print(len([f for f in json.load(sys.stdin) if f.get('passes')]))")

echo "Progress: $passing/$total features"

if [ "$passing" = "$total" ]; then
    echo ""
    echo "🎉🎉🎉 PROJECT 100% COMPLETE! 🎉🎉🎉"
    echo ""
    echo "All $total features are passing!"
    echo ""
    echo "✅ STOP WORKING - Do not add features beyond spec!"
    echo "✅ Commit final state and update progress notes"
    echo "✅ EXIT this session immediately"
    echo ""
    echo "Project is DONE. Do not continue."
    echo ""
    exit 0
fi

echo "Remaining: $((total - passing)) features"
echo "Continue with feature implementation..."
```

**Run this at the START of every session!**

**Prevents:** Scope creep, wasted compute, bugs from extra features

---

## 🛑 GATE 2: SERVICE HEALTH CHECK

**Before testing ANY features with services:**

```bash
#!/bin/bash
# Check services are healthy

if command -v docker-compose &> /dev/null; then
    echo "Checking service health..."
    
    unhealthy=$(docker-compose ps 2>/dev/null | grep -c "unhealthy" || echo "0")
    starting=$(docker-compose ps 2>/dev/null | grep -c "health: starting" || echo "0")
    
    total_waiting=$((unhealthy + starting))
    
    if [ "$total_waiting" -gt 0 ]; then
        echo "⚠️  $unhealthy unhealthy, $starting starting - waiting for services..."
        
        # Wait up to 3 minutes
        for i in {1..36}; do
            sleep 5
            unhealthy=$(docker-compose ps 2>/dev/null | grep -c "unhealthy" || echo "0")
            starting=$(docker-compose ps 2>/dev/null | grep -c "health: starting" || echo "0")
            total_waiting=$((unhealthy + starting))
            
            if [ "$total_waiting" -eq 0 ]; then
                echo "✅ All services healthy!"
                break
            fi
            
            echo "  Waiting... ($i/36)"
        done
        
        if [ "$total_waiting" -gt 0 ]; then
            echo "❌ Services still not healthy after 3 minutes!"
            echo ""
            docker-compose ps
            echo ""
            echo "Fix service health before testing features!"
            exit 1
        fi
    else
        echo "✅ All services healthy"
    fi
fi
```

**Prevents:** Testing against broken services (403, 500 errors)

---

## 🛑 GATE 3: DATABASE SCHEMA VALIDATION

**For features using database, BEFORE marking passing:**

```python
#!/usr/bin/env python3
# validate_schema.py

import psycopg2
import sys
from typing import List, Tuple

def check_table_columns(conn, table_name: str, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """Check if all required columns exist in table."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
    """, (table_name,))
    
    existing = {row[0] for row in cursor.fetchall()}
    missing = [col for col in required_columns if col not in existing]
    
    return len(missing) == 0, missing

# Usage in feature implementation:
# 1. Identify tables/columns used by feature
# 2. Run validation
# 3. If missing columns: Create migration FIRST!
# 4. Only then test feature

# Example:
conn = psycopg2.connect(DATABASE_URL)

# Check files table has required columns
valid, missing = check_table_columns(conn, 'files', [
    'id', 'title', 'owner_id', 'canvas_data',
    'version_count', 'collaborator_count', 'comment_count',
    'retention_policy', 'retention_count', 'retention_days',
    'size_bytes', 'last_activity', 'last_accessed_at'
])

if not valid:
    print(f"❌ Missing columns in 'files': {missing}")
    print("Create migration to add these columns!")
    sys.exit(1)

print("✅ Database schema validated")
```

**Prevents:** Runtime schema errors, missing column exceptions

---

## 🛑 GATE 4: BROWSER INTEGRATION TEST

**For features with frontend + backend, MANDATORY:**

```markdown
### Browser Integration Test (CORS Verification)

1. **Open Browser DevTools** (F12)

2. **Navigate to feature:**
   http://localhost:3000/[feature-page]

3. **Trigger feature** (click button, submit form, etc.)

4. **Check Network Tab:**
   - Find the API request
   - Status should be: **200 OK** (not 0, not CORS error!)
   - Response has expected data
   - Request completed successfully

5. **Check Console Tab:**
   - **Zero red errors**
   - **No CORS warnings:** "blocked by CORS policy"
   - **No network failures**

6. **If CORS Error Found:**
   ```python
   # Add CORS middleware to backend
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
   
   **Re-test until browser shows 200 OK!**

**DO NOT mark feature as passing if:**
- ❌ curl works but browser fails (CORS issue!)
- ❌ Console shows red errors
- ❌ Network tab shows failed requests

**Only mark passing when browser test succeeds!**
```

**Prevents:** CORS issues, integration failures (like AutoGraph had!)

---

## 🛑 GATE 5: END-TO-END TEST (Puppeteer)

**For UI features, MANDATORY Puppeteer test:**

```python
# E2E test template

[Tool: mcp__puppeteer__puppeteer_navigate]
   Input: {'url': 'http://localhost:3000/feature-page'}

[Tool: mcp__puppeteer__puppeteer_screenshot]
   Input: {'name': 'before-action'}

# Perform the feature action
[Tool: mcp__puppeteer__puppeteer_type]
   Input: {'element': 'input field', 'ref': '#field-id', 'text': 'test data'}

[Tool: mcp__puppeteer__puppeteer_click]
   Input: {'element': 'submit button', 'ref': 'button[type="submit"]'}

# Wait for success
[Tool: mcp__puppeteer__puppeteer_wait_for]
   Input: {'text': 'Success', 'time': 5}

[Tool: mcp__puppeteer__puppeteer_screenshot]
   Input: {'name': 'after-success'}

# Verify in database (backend check)
[Tool: Bash]
   Input: {'command': 'psql -c "SELECT * FROM table WHERE ..."'}

# Check console for errors
[Tool: mcp__puppeteer__puppeteer_console_messages]
   # Should have no errors!
```

**Must test:**
- Complete user workflow (not just API!)
- UI updates correctly
- Data persists in database
- No console errors

**Prevents:** UI bugs, integration failures, broken workflows

---

## 🛑 GATE 6: ZERO TODOs POLICY

**Before marking feature as passing:**

```bash
#!/bin/bash
# Check for TODOs in modified files

echo "Checking for TODOs in modified files..."

# Get files modified in this session
modified_files=$(git diff --name-only HEAD)

if [ -z "$modified_files" ]; then
    echo "No modified files to check"
    exit 0
fi

# Search for TODOs
todos_found=$(echo "$modified_files" | xargs grep -n "TODO\|FIXME\|WIP\|HACK" 2>/dev/null || true)

if [ -n "$todos_found" ]; then
    echo "❌ TODOs found in modified files:"
    echo "$todos_found"
    echo ""
    echo "Options:"
    echo "1. Complete the TODO implementation"
    echo "2. Remove the TODO comment"
    echo "3. Leave feature as 'passes': false (defer to next session)"
    echo ""
    echo "DO NOT mark feature as passing with TODOs!"
    exit 1
fi

echo "✅ No TODOs found in modified files"
```

**Exception:** Documentation TODOs OK, implementation TODOs NOT OK!

**Prevents:** Incomplete implementations marked as complete (like email TODOs!)

---

## 🛑 GATE 7: SECURITY CHECKLIST

**For authentication, authorization, or sensitive data features:**

```markdown
### Security Verification Checklist

Run through this checklist:

**Authentication:**
- [ ] No credentials in URLs (use POST with body, NEVER GET!)
  ```bash
  grep -r "password.*GET\|token.*GET" . && echo "❌ SECURITY ISSUE!"
  ```
- [ ] Passwords hashed with bcrypt (cost 12+)
  ```python
  # Verify:
  import bcrypt
  bcrypt.gensalt(rounds=12)  # Cost factor 12
  ```
- [ ] JWT tokens expire (< 24 hours for access tokens)
- [ ] Tokens stored securely (httpOnly cookies or secure storage)

**Input Validation:**
- [ ] All inputs validated (Pydantic models, schema validation)
- [ ] SQL injection prevention (ORMs only, NO raw SQL with f-strings!)
  ```bash
  grep -r "execute.*f\"\|execute.*%" . && echo "⚠️ SQL INJECTION RISK!"
  ```
- [ ] XSS prevention (escape HTML outputs, sanitize user input)

**API Security:**
- [ ] Rate limiting on auth endpoints (prevent brute force)
- [ ] CORS configured correctly (not allow_origins=["*"] in production!)

**Secrets:**
- [ ] No hardcoded secrets in code
  ```bash
  grep -r "password.*=.*['\"].*['\"]" . && echo "❌ HARDCODED SECRET!"
  ```
- [ ] Environment variables for secrets
- [ ] .env.example provided (not real .env!)

**Automated Check:**
```bash
./check_security.sh
# Should pass all checks!
```

**DO NOT mark security features as passing without 100% checklist completion!**
```

**Prevents:** Security vulnerabilities (like credentials in URLs!)

---

## 🛑 GATE 8: REGRESSION TEST (Every 5 Sessions)

**After every 5 sessions, run regression tests:**

```python
#!/usr/bin/env python3
# regression_test.py

import json
import random
import subprocess

# Load features
features = json.load(open('feature_list.json'))
passing_features = [f for f in features if f.get('passes')]

if len(passing_features) == 0:
    print("No passing features to test yet")
    exit(0)

# Test 10% random sample (minimum 5, maximum 50)
sample_size = max(5, min(50, len(passing_features) // 10))
sample = random.sample(passing_features, sample_size)

print(f"Running regression tests on {sample_size} random features...")
print("=" * 60)

failures = []

for i, feature in enumerate(sample, 1):
    print(f"\n[{i}/{sample_size}] Testing: {feature['description'][:60]}...")
    
    # Re-execute feature test steps
    try:
        # Parse and execute test steps
        # (Implementation depends on feature type)
        result = test_feature(feature)
        
        if result:
            print("  ✅ Pass")
        else:
            print("  ❌ REGRESSION!")
            failures.append(feature)
    
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        failures.append(feature)

print("\n" + "=" * 60)

if failures:
    print(f"\n❌ REGRESSIONS FOUND: {len(failures)}/{sample_size}")
    print("\nFailed features:")
    for f in failures:
        print(f"  - {f['description']}")
    print("\n🛑 FIX REGRESSIONS before continuing with new features!")
    exit(1)
else:
    print(f"\n✅ All {sample_size} regression tests passed!")
    print("Safe to continue with new features.")
```

**Run every 5 sessions!**

**Prevents:** Old features breaking when adding new ones

---

## ✅ All 8 Gates Documented!

**These prevent AutoGraph-type issues:**
1. ✅ Stop condition (no scope creep)
2. ✅ Service health (no testing broken services)
3. ✅ Schema validation (no missing columns)
4. ✅ Browser integration (no CORS issues)
5. ✅ E2E testing (no broken workflows)
6. ✅ Zero TODOs (no incomplete code)
7. ✅ Security (no credential leaks)
8. ✅ Regression (no breaking changes)

**Ready to integrate into prompts!**

