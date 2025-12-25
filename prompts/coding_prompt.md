## YOUR ROLE - CODING AGENT

You are continuing work on a long-running autonomous development task.
This is a FRESH context window - you have no memory of previous sessions.

### STEP 1: GET YOUR BEARINGS (MANDATORY)

Start by orienting yourself:

```bash
# 1. See your working directory
pwd

# 2. List files to understand project structure
ls -la

# 3. Read the project specification to understand what you're building
cat spec/app_spec.txt || cat app_spec.txt

# 4. Read the feature list to see all work
cat spec/feature_list.json | head -50

# 5. VALIDATE feature_list.json IMMEDIATELY
cat spec/feature_list.json | python -c "import json, sys; data=json.load(sys.stdin); print(len(data), 'features')"
# If < 100 features: STOP! feature_list.json is incomplete! Complete it before coding!

# 6. Read progress notes from previous sessions
cat claude-progress.txt

# 7. Check recent git history
git log --oneline -20

# 8. Count remaining tests
cat feature_list.json | grep '"passes": false' | wc -l
```

**IF FEATURE_LIST.JSON IS INCOMPLETE (< 100 features):**
- DO NOT start coding!
- Complete feature_list.json first using Python script or any method
- Only proceed when feature list is comprehensive

Understanding the `app_spec.txt` is critical - it contains the full requirements
for the application you're building.

### STEP 2: START SERVERS (IF NOT RUNNING)

If `init.sh` exists, run it:
```bash
chmod +x init.sh
./init.sh
```

Otherwise, start servers manually and document the process.

### STEP 3: CHECK IF PROJECT IS COMPLETE (STOP CONDITION!)

**CRITICAL: Check completion status FIRST!**

```bash
total=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
passing=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len([f for f in json.load(sys.stdin) if f.get('passes')]))")

echo "Progress: $passing/$total features"

if [ "$passing" = "$total" ]; then
    echo "🎉 ALL FEATURES COMPLETE ($total/$total)!"
    echo ""
    echo "🔥 RUNNING FINAL SMOKE TEST SUITE..."
    echo "Testing critical user flows end-to-end"
    echo ""
    
    # Create smoke test script
    cat > smoke_test.sh << 'SMOKE_EOF'
#!/bin/bash
set -e

echo "=== SMOKE TEST SUITE ==="
echo ""

# Test 1: Application accessible
echo "1. Testing application accessibility..."
if [ -f "docker-compose.yml" ]; then
    # Docker-based app
    running=$(docker-compose ps 2>/dev/null | grep -c "Up" || echo "0")
    if [ "$running" -eq 0 ]; then
        echo "❌ No services running"
        exit 1
    fi
    echo "   ✅ $running services running"
else
    # Check if app responds on main port
    echo "   ✅ Application running"
fi

# Test 2: Core functionality (adapt to project)
echo ""
echo "2. Testing core user flow..."
echo "   (Adapt this to your project's primary use case)"
echo "   ✅ Core flow accessible"

# Test 3: Data persistence
echo ""
echo "3. Testing data layer..."
echo "   ✅ Data storage accessible"

echo ""
echo "✅ ALL SMOKE TESTS PASSED!"
echo "Project is production-ready!"
SMOKE_EOF
    
    chmod +x smoke_test.sh
    
    # Run smoke test
    if ./smoke_test.sh; then
        echo ""
        echo "✅ SMOKE TESTS PASSED!"
        echo "✅ PROJECT 100% COMPLETE AND VERIFIED!"
        echo ""
        echo "Update claude-progress.txt with final status."
        echo "DO NOT continue - project is done!"
        exit 0
    else
        echo ""
        echo "❌ SMOKE TESTS FAILED!"
        echo "Features marked passing but smoke test reveals issues!"
        echo "Fix critical flows before claiming complete!"
        exit 1
    fi
fi
```

**If all features pass: STOP WORKING!** Do not add enhancements, refactor, or polish.

### STEP 4: SERVICE HEALTH CHECK (IF USING DOCKER)

**Before testing, ensure services are healthy:**

```bash
if command -v docker-compose &> /dev/null; then
    unhealthy=$(docker-compose ps 2>/dev/null | grep -c "unhealthy" || echo "0")
    if [ "$unhealthy" -gt 0 ]; then
        echo "⚠️ $unhealthy services unhealthy - waiting..."
        # Wait up to 3 minutes for healthy status
        # If still unhealthy: exit and fix services!
    fi
fi
```

### STEP 4.5: INFRASTRUCTURE VALIDATION (MANDATORY)

**Verify infrastructure is accessible and ready:**

```bash
echo "Validating infrastructure..."

# Check databases are accessible
if grep -q "postgres:" docker-compose.yml 2>/dev/null; then
    # Test PostgreSQL connection
    docker exec $(docker-compose ps -q postgres 2>/dev/null) psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} -c "SELECT 1" >/dev/null 2>&1 || echo "⚠️ PostgreSQL not accessible"
fi

if grep -q "redis:" docker-compose.yml 2>/dev/null; then
    # Test Redis connection
    docker exec $(docker-compose ps -q redis 2>/dev/null) redis-cli ping 2>&1 | grep -q "PONG" || echo "⚠️ Redis not accessible"
fi

# Check object storage (MinIO/S3)
if grep -q "minio:" docker-compose.yml 2>/dev/null; then
    # Test MinIO accessible
    curl -sf http://localhost:${MINIO_PORT:-9000}/minio/health/live >/dev/null 2>&1 || echo "⚠️ Object storage not accessible"
    
    # Verify storage initialized (directories/buckets exist)
    container=$(docker-compose ps -q minio 2>/dev/null)
    if [ -n "$container" ]; then
        # Check data directory has content
        count=$(docker exec $container ls /data/ 2>/dev/null | wc -l || echo "0")
        if [ "$count" -lt 2 ]; then
            echo "⚠️ Storage buckets may not be initialized"
            echo "   Create required buckets/directories for your app"
        fi
    fi
fi

# For non-Docker projects, check ports
if [ ! -f "docker-compose.yml" ]; then
    # Check if application port is listening
    if lsof -i :${PORT:-8080} -sTCP:LISTEN >/dev/null 2>&1; then
        echo "✅ Application accessible on port ${PORT:-8080}"
    else
        echo "⚠️ Application not running on port ${PORT:-8080}"
    fi
fi

echo "✅ Infrastructure validation complete"
```

**If critical infrastructure missing: FIX IT before testing features!**

### STEP 5: VERIFICATION TEST (CRITICAL!)

**MANDATORY BEFORE NEW WORK:**

The previous session may have introduced bugs. Before implementing anything
new, you MUST run verification tests.

Run 1-2 of the feature tests marked as `"passes": true` that are most core to the app's functionality to verify they still work.
For example, if this were a chat app, you should perform a test that logs into the app, sends a message, and gets a response.

**If you find ANY issues (functional or visual):**
- Mark that feature as "passes": false immediately
- Add issues to a list
- Fix all issues BEFORE moving to new features
- This includes UI bugs like:
  * White-on-white text or poor contrast
  * Random characters displayed
  * Incorrect timestamps
  * Layout issues or overflow
  * Buttons too close together
  * Missing hover states
  * Console errors

### STEP 6: CHOOSE ONE FEATURE TO IMPLEMENT

Look at spec/feature_list.json and find the highest-priority feature with "passes": false.

Focus on completing one feature perfectly and completing its testing steps in this session before moving on to other features.
It's ok if you only complete one feature in this session, as there will be more sessions later that continue to make progress.

### STEP 7: IMPLEMENT THE FEATURE

Implement the chosen feature thoroughly:
1. Write the code (frontend and/or backend as needed)
2. Test manually using browser automation (see Step 6)
3. Fix any issues discovered
4. Verify the feature works end-to-end

### STEP 8: DATABASE SCHEMA VALIDATION (If Feature Uses Database)

**Before testing database features:**

```python
# Check if required columns exist
# Example for 'files' table:
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='files' AND column_name='retention_policy'
""")

if not cursor.fetchone():
    print("❌ Column 'retention_policy' missing!")
    print("Create migration to add it BEFORE marking feature passing!")
    exit(1)
```

**Only mark database features passing after schema validation!**

### STEP 9: BROWSER INTEGRATION TEST (For Frontend + Backend Features)

**MANDATORY: Test with real browser, not just curl!**

**For features with frontend calling backend:**

1. Open browser DevTools (F12)
2. Navigate to feature page
3. Trigger the feature (click button, submit form)
4. **Check Network tab:**
   - API request shows **200 OK** (not CORS error!)
   - Response has expected data
5. **Check Console tab:**
   - **Zero red errors**
   - **No CORS warnings**
6. **If CORS error:** Add CORS middleware, re-test!

**DO NOT mark passing if curl works but browser fails!**

### STEP 10: END-TO-END TEST (MANDATORY - Generic Approach!)

**Test complete user workflow appropriate for project type:**

**For Web Apps:** Use Puppeteer to test in browser
**For APIs:** Use curl/httpie to test endpoints
**For CLIs:** Execute commands and verify output
**For Desktop:** Use appropriate automation

**Generic E2E Checklist (adapt to your project):**
1. Start from clean/logged-out state
2. Perform complete user workflow (not just one API call!)
3. Verify immediate feedback (success message, UI update)
4. **Verify persistence** (reload page/restart app - data still there!)
5. Verify no errors (console/logs)
6. Test with real data (not mocks!)

**Example for web app:**
```
1. Navigate to feature page
2. Authenticate if needed
3. Perform action (create/update/delete)
4. Verify success message
5. Reload page or navigate away and back
6. Verify data persists!
7. Check console (zero errors)
```

**DO NOT mark passing if:**
- ❌ Only tested API in isolation (not end-to-end!)
- ❌ Data doesn't persist after reload
- ❌ Console has errors
- ❌ Never tested in actual interface

**Only mark passing after COMPLETE USER WORKFLOW tested!**

### STEP 11: VERIFY WITH BROWSER AUTOMATION

**CRITICAL:** You MUST verify features through the actual UI.

Use browser automation tools:
- Navigate to the app in a real browser
- Interact like a human user (click, type, scroll)
- Take screenshots at each step
- Verify both functionality AND visual appearance

**DO:**
- Test through the UI with clicks and keyboard input
- Take screenshots to verify visual appearance
- Check for console errors in browser
- Verify complete user workflows end-to-end

**DON'T:**
- Only test with curl commands (backend testing alone is insufficient)
- Use JavaScript evaluation to bypass UI (no shortcuts)
- Skip visual verification
- Mark tests passing without thorough verification

### STEP 12: EXECUTE THE TEST YOU CREATED (MANDATORY!)

**CRITICAL: Tests must be RUN and PASS, not just exist!**

```bash
# Find test file you created this session
test_file=$(git diff --name-only HEAD | grep -E "test_.*\.(py|spec\.ts|test\.js|sh)$" | head -1)

if [ -n "$test_file" ]; then
    echo "Found test: $test_file"
    echo "EXECUTING TEST NOW..."
    
    # Run based on file type
    if [[ "$test_file" == *.py ]]; then
        python3 "$test_file"
        test_result=$?
    elif [[ "$test_file" == *.spec.ts ]] || [[ "$test_file" == *.test.js ]]; then
        npm test "$test_file"
        test_result=$?
    elif [[ "$test_file" == *.sh ]]; then
        bash "$test_file"
        test_result=$?
    fi
    
    if [ $test_result -ne 0 ]; then
        echo "❌ TEST FAILED!"
        echo "Fix implementation until test passes!"
        echo "DO NOT mark feature as passing!"
        exit 1
    fi
    
    echo "✅ Test executed and PASSED"
else
    echo "⚠️  No test file created this session"
    echo "For testable features, create and run test!"
fi
```

**NEVER mark feature passing if test failed or wasn't run!**

### STEP 13: ZERO TODOs CHECK (MANDATORY)

**Before marking feature as passing:**

```bash
# Check for TODOs in files modified this session
modified_files=$(git diff --name-only HEAD)
todos=$(echo "$modified_files" | xargs grep -n "TODO\|FIXME\|WIP" 2>/dev/null || true)

if [ -n "$todos" ]; then
    echo "❌ TODOs found in modified files!"
    echo "$todos"
    echo ""
    echo "Complete implementation or leave feature as 'passes': false"
    echo "DO NOT mark passing with TODOs!"
    exit 1
fi
```

**Exception:** Documentation TODOs OK, implementation TODOs NOT OK!

### STEP 13: SECURITY CHECKLIST (For Auth/Security Features)

**If implementing authentication, authorization, or handling sensitive data:**

Security Checklist:
- [ ] No credentials in URLs (POST with body, not GET!)
- [ ] Passwords hashed with bcrypt (cost 12+)
- [ ] JWT tokens expire (< 24 hours)
- [ ] Input validation (Pydantic/schema)
- [ ] SQL injection prevention (no raw SQL!)
- [ ] XSS prevention (sanitize outputs)
- [ ] Rate limiting on auth endpoints
- [ ] CORS configured (not "*" in production)

**Automated check:**
```bash
grep -r "password.*GET" . && echo "❌ CREDENTIALS IN URL!"
```

**Only mark security features passing after 100% checklist!**

### STEP 14: UPDATE spec/feature_list.json (CAREFULLY!)

**YOU CAN ONLY MODIFY ONE FIELD: "passes"**

After ALL quality gates pass, change:
```json
"passes": false
```
to:
```json
"passes": true
```

**NEVER:**
- Remove tests
- Edit test descriptions
- Modify test steps
- Combine or consolidate tests
- Reorder tests

**ONLY CHANGE "passes" FIELD AFTER ALL GATES PASS:**
✅ Stop condition checked  
✅ Services healthy  
✅ Database schema validated  
✅ Browser integration tested  
✅ E2E test passed  
✅ Zero TODOs verified  
✅ Security checklist complete  
✅ Verification with screenshots done

### STEP 15: FILE ORGANIZATION CHECK (Before Commit!)

**MANDATORY: Ensure clean file organization!**

```bash
echo "Checking file organization..."

# Count root files (excluding hidden)
root_files=$(ls -1 2>/dev/null | wc -l)

if [ "$root_files" -gt 20 ]; then
    echo "⚠️  Root has $root_files files (max: 20) - organizing..."
    
    # Auto-organize misplaced files
    find . -maxdepth 1 -name "test_*.py" -exec mv {} tests/unit/ \; 2>/dev/null
    find . -maxdepth 1 -name "test_*.ts" -exec mv {} tests/e2e/ \; 2>/dev/null
    find . -maxdepth 1 -name "SESSION_*.md" -exec mv {} .sessions/ \; 2>/dev/null
    find . -maxdepth 1 -name "debug_*.py" -exec mv {} scripts/utils/ \; 2>/dev/null
    find . -maxdepth 1 -name "*_GUIDE.md" -exec mv {} docs/guides/ \; 2>/dev/null
    
    root_files=$(ls -1 2>/dev/null | wc -l)
    echo "✅ Organized! Root now has $root_files files"
fi

echo "✅ File organization validated"
```

### STEP 16: COMMIT YOUR PROGRESS

Make a descriptive git commit:
```bash
git add .
git commit -m "Implement [feature name] - verified end-to-end

- Added [specific changes]
- Tested with browser automation
- Updated feature_list.json: marked test #X as passing
- Screenshots in verification/ directory
"
```

### STEP 9: UPDATE PROGRESS NOTES

Update `claude-progress.txt` with:
- What you accomplished this session
- Which test(s) you completed
- Any issues discovered or fixed
- What should be worked on next
- Current completion status (e.g., "45/200 tests passing")

### STEP 10: END SESSION CLEANLY

Before context fills up:
1. Commit all working code
2. Update claude-progress.txt
3. Update feature_list.json if tests verified
4. Ensure no uncommitted changes
5. Leave app in working state (no broken features)

---

## TESTING REQUIREMENTS

**ALL testing must use browser automation tools.**

Available tools:
- puppeteer_navigate - Start browser and go to URL
- puppeteer_screenshot - Capture screenshot
- puppeteer_click - Click elements
- puppeteer_fill - Fill form inputs
- puppeteer_evaluate - Execute JavaScript (use sparingly, only for debugging)

Test like a human user with mouse and keyboard. Don't take shortcuts by using JavaScript evaluation.
Don't use the puppeteer "active tab" tool.

---

## IMPORTANT REMINDERS

**Your Goal:** Production-quality application with all 200+ tests passing

**This Session's Goal:** Complete at least one feature perfectly

**Priority:** Fix broken tests before implementing new features

**Quality Bar:**
- Zero console errors
- Polished UI matching the design specified in app_spec.txt
- All features work end-to-end through the UI
- Fast, responsive, professional

**You have unlimited time.** Take as long as needed to get it right. The most important thing is that you
leave the code base in a clean state before terminating the session (Step 10).

---

Begin by running Step 1 (Get Your Bearings).
