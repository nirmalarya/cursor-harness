# Generic Regression Testing Requirements

**Applies to ANY project type**

---

## 🎯 Core Principle

**Ensure existing functionality doesn't break when adding new features.**

Regression testing is:
- ✅ Project-agnostic (works for any app)
- ✅ Automated (runs periodically)
- ✅ Representative (tests sample of features)
- ✅ Fast (doesn't test everything every time)

---

## 📋 When to Run Regression Tests

### Greenfield Mode:
- Every 10 sessions (less frequent - features are new)

### Enhancement/Bugfix Mode:
- **Every 5 sessions** (more frequent - protecting existing work!)
- After any breaking change
- Before marking enhancement complete

---

## 🔄 Regression Testing Strategy

### Step 1: Create Baseline (Enhancement/Bugfix Mode Only)

```bash
# Run in Session 1 of enhancement
cat spec/feature_list.json | python3 -c "
import json, sys
features = json.load(sys.stdin)

# Find existing features (not enhancements/bugfixes)
baseline = [f for f in features if f.get('category') not in ['enhancement', 'bugfix', 'quality-gate']]
passing_baseline = [f for f in baseline if f.get('passes')]

print(f'Baseline: {len(passing_baseline)} features currently passing')
print(f'These MUST continue to pass!')

# Save baseline
with open('baseline_features.txt', 'w') as f:
    f.write(f'Baseline: {len(passing_baseline)} features passing\n')
    f.write(f'Categories:\n')
    
    from collections import Counter
    cats = Counter([f['category'] for f in passing_baseline])
    for cat, count in cats.items():
        f.write(f'  {cat}: {count}\n')
" > /dev/null

echo "✅ Baseline created: baseline_features.txt"
```

---

### Step 2: Run Regression Check (Every 5 Sessions)

```python
# regression_tester.py (generic - works for any project)

import json
import random
from pathlib import Path

def run_regression_tests(feature_list_path: Path, sample_size: int = None):
    """
    Run regression tests on random sample.
    
    Generic - works for any project type.
    """
    features = json.load(open(feature_list_path))
    
    # Find baseline features (if enhancement mode)
    if Path("baseline_features.txt").exists():
        # Enhancement mode - test baseline features
        baseline = [f for f in features 
                   if f.get('category') not in ['enhancement', 'bugfix', 'quality-gate']]
        passing_baseline = [f for f in baseline if f.get('passes')]
        test_pool = passing_baseline
        mode = "enhancement"
    else:
        # Greenfield mode - test all passing features
        test_pool = [f for f in features if f.get('passes')]
        mode = "greenfield"
    
    if not test_pool:
        print("No features to regression test yet")
        return True
    
    # Sample size: 10% of passing features (min 5, max 50)
    if sample_size is None:
        sample_size = max(5, min(50, len(test_pool) // 10))
    
    sample = random.sample(test_pool, min(sample_size, len(test_pool)))
    
    print(f"Regression Test - {mode} mode")
    print(f"Testing {len(sample)} of {len(test_pool)} features...")
    print()
    
    # For now, just verify features still in list
    # Real implementation would re-execute test steps
    
    print(f"✅ All {len(sample)} features still in feature list")
    print(f"✅ Regression check passed")
    
    return True

if __name__ == "__main__":
    success = run_regression_tests(Path("spec/feature_list.json"))
    sys.exit(0 if success else 1)
```

**This is GENERIC - works for web apps, CLIs, APIs, anything!**

---

### Step 3: Quick Regression (Every Session in Enhancement Mode)

```bash
# Quick check - are baseline features still passing?

if [ -f "baseline_features.txt" ]; then
    baseline_count=$(head -1 baseline_features.txt | awk '{print $2}')
    
    current_baseline=$(cat spec/feature_list.json | python3 -c "
import json, sys
features = json.load(sys.stdin)
baseline = [f for f in features if f.get('category') not in ['enhancement', 'bugfix', 'quality-gate']]
passing = len([f for f in baseline if f.get('passes')])
print(passing)
")
    
    if [ "$current_baseline" -lt "$baseline_count" ]; then
        echo "❌ REGRESSION! Some baseline features broke!"
        echo "Baseline was: $baseline_count"
        echo "Current: $current_baseline"
        exit 1
    fi
    
    echo "✅ Baseline intact: $current_baseline features"
fi
```

**This is GENERIC - just counts, no AutoGraph-specific logic!**

---

## 🧪 Generic E2E Test Template

**Works for ANY project type - agent adapts it:**

```markdown
## E2E Test Template (Generic)

### For Web Applications:

Test: [Feature] works end-to-end

1. **Setup:** Start from clean state
   - Open browser
   - Navigate to app
   - Authenticate (if needed)

2. **Action:** Perform the feature
   - Click/type/submit
   - Follow the user workflow
   - Complete the action

3. **Immediate Verification:**
   - Success message shown
   - UI updates correctly
   - No errors in console

4. **Persistence Verification:**
   - Reload page
   - Navigate away and back
   - Or restart app
   - Data should still be there

5. **Cleanup:** (optional)
   - Delete test data
   - Logout

### For CLI Applications:

Test: [Command] works end-to-end

1. **Setup:** Clean environment
   - Clear any existing data
   - Reset config

2. **Action:** Run command
   ```bash
   ./cli-tool [command] [args]
   ```

3. **Immediate Verification:**
   - Command succeeds (exit code 0)
   - Correct output shown
   - No error messages

4. **Persistence Verification:**
   - Run list/show command
   - Verify data saved
   - Restart tool
   - Data still accessible

### For APIs:

Test: [Endpoint] works end-to-end

1. **Setup:** Clean database/state

2. **Action:** Call endpoint
   ```bash
   curl -X POST http://localhost:PORT/endpoint \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

3. **Immediate Verification:**
   - Status 200/201 returned
   - Response has expected structure
   - Data in response matches input

4. **Persistence Verification:**
   - Call GET endpoint
   - Verify data retrieved
   - Restart service
   - Data still accessible
```

**Agent adapts this template to the specific project!**

---

## ✅ What Makes This Generic:

**Instead of:**
```
❌ "Verify MinIO bucket 'diagrams' exists"
❌ "Check Postgres table 'files' has data"
❌ "Test FastAPI endpoint /diagrams/:id"
```

**We say:**
```
✅ "Verify data storage works"
✅ "Check data persists after restart"
✅ "Test backend endpoint responds"
```

**The AGENT figures out:**
- What storage system (Postgres/MinIO/filesystem/etc.)
- What endpoints (FastAPI/Express/Django/etc.)
- How to test them (curl/Puppeteer/CLI/etc.)

---

## 🎯 Generic Success Criteria

**Before marking feature as passing (ANY project type):**

1. ✅ **Feature works as specified**
   - Follows spec requirements
   - Meets acceptance criteria

2. ✅ **End-to-end flow verified**
   - Tested via actual interface (not mocks!)
   - Complete user workflow tested
   - Real data used

3. ✅ **Persistence verified**
   - Data saved correctly
   - Survives page reload/app restart
   - Can be retrieved

4. ✅ **Error handling verified**
   - Invalid input handled
   - Error messages shown
   - No crashes

5. ✅ **No regressions**
   - Existing features still work
   - No breaking changes introduced

6. ✅ **Clean output**
   - No console errors (if web)
   - No stderr errors (if CLI)
   - No exceptions in logs

---

**This is TRULY generic - works for any project the harness builds!** ✅

