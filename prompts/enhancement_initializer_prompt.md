## YOUR ROLE - ENHANCEMENT INITIALIZER

You are ENHANCING an existing project (not building from scratch).

This is Session 1 of enhancement mode.

---

## CRITICAL: This is ENHANCEMENT MODE

**You are NOT building a new project!**
**You are ADDING features to an existing codebase!**

---

### STEP 1: UNDERSTAND EXISTING PROJECT

**Scan the existing codebase:**

```bash
# 1. Check what exists
pwd
ls -la

# 2. Check if feature_list.json already exists
if [ -f "spec/feature_list.json" ]; then
    echo "✅ Existing spec/feature_list.json found"
    total=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
    passing=$(cat spec/feature_list.json | python3 -c "import json, sys; print(len([f for f in json.load(sys.stdin) if f.get('passes')]))")
    echo "Current state: $passing/$total features passing"
else
    echo "⚠️ No spec/feature_list.json - might be new enhancement"
fi

# 3. Read the enhancement spec
cat spec/enhancement_spec.txt || cat spec/app_spec.txt

# 4. Check git history (understand what was built)
git log --oneline -20

# 5. Scan for TODOs, FIXMEs, bugs
grep -r "TODO\|FIXME\|WIP\|BUG" --include="*.py" --include="*.ts" --include="*.tsx" . | head -20

# 6. Check README
cat README.md | head -50
```

---

### STEP 2: READ ENHANCEMENT SPECIFICATION

**The enhancement_spec.txt tells you what to add/fix:**

```xml
<enhancement_spec>
  <enhancements>
    <!-- New features to add -->
  </enhancements>
  
  <bugfixes>
    <!-- Issues to fix -->
  </bugfixes>
  
  <quality_improvements>
    <!-- TODOs to complete, etc -->
  </quality_improvements>
</enhancement_spec>
```

**Understand:**
- What features to add
- What bugs to fix
- What to preserve (don't break!)

---

### STEP 3: ANALYZE EXISTING FEATURE LIST

**If feature_list.json exists:**

```python
import json

features = json.load(open('feature_list.json'))

print(f"Existing features: {len(features)}")
print(f"Passing: {len([f for f in features if f.get('passes')])}")
print(f"Last feature number: {len(features)}")

# Find highest feature number
max_num = len(features)
print(f"New features should start at: {max_num + 1}")
```

---

### STEP 4: GENERATE ENHANCEMENT FEATURE LIST

**APPEND to existing feature_list.json (don't replace!):**

```python
import json

# Load existing
existing_features = json.load(open('feature_list.json')) if os.path.exists('feature_list.json') else []
start_num = len(existing_features) + 1

# Generate new features from enhancement spec
new_features = []

# For each enhancement in spec:
new_features.append({
    "id": start_num,
    "category": "enhancement",  # or "bugfix"
    "description": "New feature description",
    "steps": [...],
    "passes": false,
    "original_feature_id": 42  # If fixing/enhancing existing feature
})

# Combine
all_features = existing_features + new_features

# Save
with open('feature_list.json', 'w') as f:
    json.dump(all_features, f, indent=2)

print(f"Added {len(new_features)} new features")
print(f"Total features: {len(all_features)}")
```

**CRITICAL:**
- Start numbering from (last existing + 1)
- Don't modify existing features
- Mark old bugs as "passes": false if broken

---

### STEP 5: CREATE REGRESSION TEST BASELINE

**Document what currently works:**

```bash
# Create baseline of passing features
cat feature_list.json | python3 -c "
import json, sys
features = json.load(sys.stdin)
passing = [f for f in features if f.get('passes')]

print(f'Baseline: {len(passing)} features currently passing')
print('Categories:')

from collections import Counter
cats = Counter([f['category'] for f in passing])
for cat, count in cats.items():
    print(f'  {cat}: {count}')
" > baseline_features.txt

echo "Baseline created: baseline_features.txt"
```

**This is what we must NOT break!**

---

### STEP 6: DOCUMENT ENHANCEMENT PLAN

**Create enhancement plan document:**

```markdown
# Enhancement Plan

## Current State
- Features: X/Y passing
- Version: vX.Y
- Issues: (list known issues)

## Enhancements to Add
1. Feature X (features #Z-W)
2. Feature Y (features #A-B)
...

## Bugs to Fix
1. Issue X (affects feature #N)
2. Issue Y (affects feature #M)
...

## Regression Requirements
- All X existing passing features must still work
- Run regression tests every 5 sessions
- No breaking changes allowed

## Success Criteria
- All enhancements working
- All bugs fixed
- Zero regressions
- All new features tested
```

**Save as:** `ENHANCEMENT_PLAN.md`

---

### STEP 7: COMMIT INITIAL STATE

```bash
git add feature_list.json baseline_features.txt ENHANCEMENT_PLAN.md
git commit -m "Session 1 (Enhancement): Initialize enhancement mode

- Analyzed existing project (X features passing)
- Read enhancement spec
- Generated enhancement feature list (Y new features)
- Created regression baseline
- Ready to start enhancements

Enhancement features: #${start_num}-${end_num}
Baseline features: ${existing_passing} must still pass"
```

---

### STEP 8: UPDATE PROGRESS NOTES

**Create or append to claude-progress.txt:**

```
================================================================================
SESSION 1: ENHANCEMENT INITIALIZER
================================================================================

Mode: Enhancement (adding features to existing project)

Existing State:
- Features: X/Y passing
- Code: (scanned)
- Issues: (TODOs found)

Enhancement Spec:
- New features: Z
- Bug fixes: W
- Quality improvements: V

Generated:
- feature_list.json (appended Y new features)
- baseline_features.txt (X features must still pass)
- ENHANCEMENT_PLAN.md

Next Session:
- Start implementing enhancements
- Run regression tests every 5 sessions
- Preserve all existing functionality

Session 1 complete. Ready for enhancement coding sessions.
================================================================================
```

---

## IMPORTANT REMINDERS

**This is ENHANCEMENT mode - special rules:**

1. **PRESERVE existing functionality**
   - All passing features must keep passing
   - No breaking changes
   - Regression tests mandatory

2. **CAREFUL changes**
   - Understand existing code before modifying
   - Small, incremental changes
   - Test after each change

3. **REGRESSION TESTING**
   - Run every 5 sessions (mandatory!)
   - If any old feature breaks: FIX IMMEDIATELY!
   - New features are worthless if old ones break

4. **QUALITY GATES STILL APPLY**
   - All 8 quality gates enforced
   - Same standards as greenfield
   - Maybe stricter (can't break existing!)

---

**Your goal:** Add enhancements WITHOUT breaking existing functionality!

**Begin with STEP 1: Understand existing project.**

