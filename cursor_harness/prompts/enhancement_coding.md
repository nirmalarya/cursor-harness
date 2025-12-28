# Enhancement Coding - Incremental Progress (Brownfield)

You are adding enhancements to an EXISTING project.

**This is a FRESH context window** - you have no memory of previous sessions.

---

## Step 1: Get Your Bearings

```bash
pwd
git log --oneline -20
cat cursor-progress.txt
cat enhancement_list.json | head -50
```

## Step 2: Check Completion

```bash
total=$(cat enhancement_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
completed=$(cat enhancement_list.json | python3 -c "import json, sys; print(len([e for e in json.load(sys.stdin) if e.get('completed')]))")
echo "$completed/$total enhancements complete"
```

If all completed, STOP - enhancements are done.

## Step 3: Understand Existing Code

Before implementing, understand the existing architecture:

```bash
# Look at project structure
find . -type f -name "*.py" -o -name "*.ts" -o -name "*.go" | head -20

# Read key files
cat package.json || cat requirements.txt || cat go.mod

# Check test structure
ls -la tests/ || ls -la test/ || ls -la __tests__/
```

## Step 4: Pick ONE Enhancement

Find first enhancement where completed: false.
Work on ONLY this enhancement.

## Step 5: Implement

1. **Write tests first** - Add tests for new functionality
2. **Implement** - Integrate with existing code
3. **Test manually** - Verify works with existing features
4. **Verify no regressions** - Run ALL tests (old + new)

**CRITICAL:** Ensure new code integrates cleanly with existing code.

## Step 6: Commit

```bash
git add .
git commit -m "feat: <enhancement description>"
```

## Step 7: Update Progress

```bash
echo "Session N: Implemented <enhancement>" >> cursor-progress.txt
```

## Step 8: Mark Enhancement Complete

Edit `enhancement_list.json` - change ONLY completed: false to completed: true for this enhancement.

**DO NOT remove or edit enhancements.**

---

**One enhancement at a time. Preserve existing functionality. Move on.**

