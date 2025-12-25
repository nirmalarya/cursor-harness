# Quality Gate #10: Test Execution (MANDATORY)

**The test must actually RUN and PASS - not just exist!**

---

## 🚨 THE PROBLEM (From AutoGraph v3.1)

**What happened:**
```python
# Agent created test_save_diagram.py ✅
# Agent marked feature #660 as passing ✅
# Agent NEVER ran: python3 test_save_diagram.py ❌
# Result: Test passes when run manually, but feature broken in browser!
```

**This is a FALSE POSITIVE - the worst kind of bug!**

---

## ✅ THE SOLUTION

### Step 1: Create Test (Already Required)

```python
# Agent creates test file
# test_feature_X.py or test_feature_X.spec.ts
```

---

### Step 2: **EXECUTE THE TEST (NEW - MANDATORY!)**

```bash
#!/bin/bash
# Execute test and verify it passes

echo "Running test for feature..."

# Detect test type and run appropriately
if [ -f "test_*.py" ]; then
    # Python test
    python3 test_*.py
    test_result=$?
elif [ -f "test_*.spec.ts" ] || [ -f "test_*.test.js" ]; then
    # JavaScript/TypeScript test
    npm test
    test_result=$?
elif [ -f "test_*.sh" ]; then
    # Bash test
    bash test_*.sh
    test_result=$?
else
    echo "❌ No test file found!"
    exit 1
fi

# Check result
if [ $test_result -eq 0 ]; then
    echo "✅ Test PASSED"
else
    echo "❌ Test FAILED - cannot mark feature as passing!"
    echo "Fix the implementation until test passes!"
    exit 1
fi
```

---

### Step 3: Verify Test Output

```markdown
**The test must:**
- Exit with code 0 (success)
- Print "✅ PASSING" or similar
- Show test steps completed
- No errors in output

**NOT acceptable:**
- Test file exists but wasn't run
- Test skipped or commented out
- Test fails but ignored
- Test mocks everything (not real)
```

---

### Step 4: Verify in Context (Not Just Isolation)

**For web apps:**
```markdown
Test must verify in BROWSER (not just curl!)

1. Run test script (creates data)
2. Open browser (http://localhost:PORT)
3. Login with test user
4. Verify feature works in UI
5. Check browser console (zero errors)

NOT enough:
❌ curl to API works (but browser fails!)
❌ Test script passes (but real user can't use it!)
```

**For CLIs:**
```markdown
Test must verify actual CLI usage

1. Run CLI command
2. Verify output correct
3. Run related commands (list/show/etc.)
4. Verify data accessible
5. Restart CLI
6. Data still there

NOT enough:
❌ Internal function works (but CLI command broken!)
❌ Test in Python passes (but bash command fails!)
```

---

## 🎯 Enforcement Strategy

**Add to coding_prompt.md (before marking passing):**

```markdown
### STEP X: EXECUTE AND VERIFY TESTS (MANDATORY!)

**You created a test - now RUN it!**

```bash
# Find the test file you created
test_file=$(ls -t test_*.py test_*.spec.ts test_*.sh 2>/dev/null | head -1)

if [ -z "$test_file" ]; then
    echo "❌ No test file found - create test first!"
    exit 1
fi

echo "Executing test: $test_file"

# Run the test based on type
case "$test_file" in
    *.py)
        python3 "$test_file"
        ;;
    *.spec.ts|*.test.js|*.test.ts)
        npm test "$test_file"
        ;;
    *.sh)
        bash "$test_file"
        ;;
esac

if [ $? -ne 0 ]; then
    echo "❌ TEST FAILED!"
    echo "Fix implementation until test passes!"
    echo "DO NOT mark feature as passing!"
    exit 1
fi

echo "✅ Test executed and PASSED"
```

**Verification:**
1. Test executed ✅
2. Test passed ✅
3. No errors ✅

**Only NOW can you mark "passes": true**

**NEVER mark passing if:**
- ❌ Test wasn't run
- ❌ Test failed
- ❌ Test skipped
- ❌ "Will test later"
```

---

## 📊 Examples from AutoGraph

### ❌ What Agent Did (WRONG):

```markdown
Session 3:
- Created test_save_diagram.py ✅
- Marked feature #660 as passing ✅
- NEVER ran the test ❌

Result: False positive!
```

### ✅ What Agent SHOULD Do (CORRECT):

```markdown
Session 3:
- Create test_save_diagram.py ✅
- RUN: python3 test_save_diagram.py ✅
- Test PASSES ✅
- Verify in browser (open and test) ✅
- Browser works ✅
- THEN mark feature #660 as passing ✅

Result: True positive!
```

---

## 🎯 Success Criteria

**Feature is ONLY passing when:**
1. ✅ Test file created
2. ✅ Test executed
3. ✅ Test passed (exit 0)
4. ✅ Verified in actual interface (browser/CLI/etc.)
5. ✅ Data persists correctly
6. ✅ No errors in logs/console

**ALL 6 must be true!**

---

**This gate prevents false positives like we saw in AutoGraph!**

