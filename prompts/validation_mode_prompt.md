# VALIDATION MODE - Verify Existing Codebase

**For brownfield projects: Test and validate existing code**

---

## 🎯 Mission

**Validate ALL existing features, even if code exists!**

**Approach:**
1. Feature marked `"passes": false` (unverified)
2. Agent checks if code exists for feature
3. Agent writes test for feature
4. Agent RUNS the test
5. If passes → mark as passing ✅
6. If fails → fix code, re-test, then mark passing

**Result:** Fully tested, validated codebase + comprehensive test suite!

---

## 🔍 Step-by-Step Process

### Step 1: Check if Feature Code Exists

```bash
# For each feature, check if implementation exists

# Example: "User can save diagram"
# Search for save-related code
grep -r "save.*diagram\|update.*diagram" services/ --include="*.py" --include="*.ts"

# Found? Good! Code exists
# Not found? Need to implement
```

---

### Step 2: Write Test for Feature

```python
# Create test that verifies the feature works

# Example: test_save_diagram_validation.py

def test_save_diagram():
    """Validate that save diagram feature works."""
    
    # 1. Setup: Create test user and diagram
    user = create_test_user()
    diagram = create_test_diagram(user)
    
    # 2. Test: Update the diagram
    response = update_diagram(diagram.id, user.id, {"title": "Updated"})
    
    # 3. Verify: Changes persisted
    saved = get_diagram(diagram.id, user.id)
    assert saved.title == "Updated"
    
    print("✅ Save diagram feature works!")
    return True
```

---

### Step 3: **RUN THE TEST** (MANDATORY!)

```bash
# Execute the test
python3 test_save_diagram_validation.py

if [ $? -eq 0 ]; then
    echo "✅ Test PASSED - feature works!"
    echo "Mark feature as passing"
else
    echo "❌ Test FAILED - feature broken!"
    echo "Fix the code until test passes"
    exit 1
fi
```

**DO NOT mark as passing without running test!**

---

### Step 4: If Test Fails - Fix Code

```markdown
If test fails:

1. Analyze failure
   - What's the error?
   - What's broken?
   - Why doesn't it work?

2. Fix the code
   - Minimal fix
   - Don't rewrite everything
   - Just fix what's broken

3. Re-run test
   - Verify test now passes
   - Repeat until green

4. Only then mark as passing
```

---

### Step 5: Build Test Suite

```markdown
As you validate features:

tests/
├── validation/
│   ├── test_auth_validation.py
│   ├── test_crud_validation.py
│   ├── test_save_validation.py
│   ├── test_api_gateway_validation.py
│   └── ...

Each test:
- ✅ Verifies feature actually works
- ✅ Tests end-to-end (not just unit)
- ✅ Can be re-run for regression
- ✅ Documents how feature should work
```

---

## 🎯 Validation Mode Workflow

**For AutoGraph with 658 features:**

```
Session 1: Mark all as unverified (passes: false)
Session 2: Validate feature #1 → Write test → Run → Pass → Mark passing
Session 3: Validate feature #2 → Write test → Run → Pass → Mark passing
...
Session 100: Validate feature #99 → Write test → Run → FAIL → Fix → Re-test → Pass → Mark passing
...
Session 658: Last feature validated
Session 659: Run full regression suite (all 658 tests!)
Session 660: All pass → 658/658 → COMPLETE with full test coverage!
```

**Result:** 
- ✅ All features validated
- ✅ Comprehensive test suite (658 tests!)
- ✅ Known broken features fixed
- ✅ Production-ready with confidence

---

## ⚠️ Realistic Timeline

**For AutoGraph (658 features):**
- ~2-3 features per session (write test, run, verify)
- ~200-300 sessions total
- ~20-30 hours of agent time
- But result: FULLY VALIDATED codebase!

---

## 🎯 Let Me Implement This Now

Should I:
1. Mark ALL 658 features as `"passes": false` in AutoGraph?
2. Update the bugfix spec to explain validation approach?
3. Run the harness in "validation mode"?

**This will take time but gives you a FULLY tested codebase!**

**Want me to do this?** 🚀

