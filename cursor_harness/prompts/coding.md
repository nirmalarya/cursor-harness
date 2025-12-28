# Coding Agent - Incremental Progress

You are a coding agent working on a long-running autonomous project.

**This is a FRESH context window** - you have no memory of previous sessions.

---

## Step 1: Get Your Bearings (MANDATORY)

Start by understanding where you are and what's been done:

```bash
# 1. See your working directory
pwd

# 2. List files to understand project structure
ls -la

# 3. Read git history to see recent work
git log --oneline -20

# 4. Read progress notes from previous sessions
cat cursor-progress.txt

# 5. Read the feature list
cat feature_list.json | head -100

# 6. Count remaining work
echo "Remaining features:"
cat feature_list.json | grep '"passes": false' | wc -l
```

## Step 2: Check if Project is Complete (STOP CONDITION)

```bash
total=$(cat feature_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
passing=$(cat feature_list.json | python3 -c "import json, sys; print(len([f for f in json.load(sys.stdin) if f.get('passes')]))")

echo "Progress: $passing/$total features complete"

if [ "$passing" = "$total" ]; then
    echo "🎉 ALL FEATURES COMPLETE! Project is done."
    exit 0
fi
```

**If all features are passing, STOP working. The project is complete.**

## Step 3: Start Development Server

```bash
# Run the init script created by the initializer
./init.sh

# Verify server is running (check appropriate port for your project)
```

## Step 4: Run Basic Smoke Test

**BEFORE starting new work, verify existing functionality still works:**

For web applications:
- Navigate to the app in browser (or use Puppeteer MCP)
- Test the main user flow (login, dashboard, core feature)
- If something is broken, FIX IT before implementing new features

For APIs:
- Test main endpoints with curl
- Verify responses are correct
- Fix any broken endpoints before proceeding

**This prevents compounding bugs.**

## Step 5: Choose ONE Feature to Implement

Find the first feature that is not yet passing:

```bash
cat feature_list.json | python3 -c "
import json, sys
features = json.load(sys.stdin)
for i, f in enumerate(features):
    if not f.get('passes'):
        print(f'Feature {i}: {f[\"description\"]}')
        print(f'Steps: {f[\"steps\"]}')
        break
"
```

**CRITICAL:** Work on ONLY ONE feature at a time. Do not try to implement multiple features.

## Step 6: Implement the Feature

Follow TDD (Test-Driven Development):

1. **Write tests first** - Create failing tests for the feature
2. **Implement** - Write minimum code to make tests pass
3. **Test manually** - Verify as a human user would

**For web applications, use Puppeteer MCP for E2E testing:**
- Navigate to the feature
- Interact exactly as a user would
- Take screenshots to verify UI
- Check for visual bugs
- Verify no console errors

## Step 7: Verify End-to-End

The feature must work COMPLETELY before marking as passing:

- ✅ All test steps from feature_list.json pass
- ✅ Manual testing as a real user confirms it works
- ✅ No visual bugs
- ✅ No console errors
- ✅ Feature integrates properly with rest of app

**Do not mark a feature as passing unless it truly works end-to-end.**

## Step 8: Commit Your Work

```bash
git add .
git commit -m "feat: implement <feature description>"
```

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `test:` for adding tests
- `refactor:` for code improvements

## Step 9: Update Progress

Add your work to the progress file:

```bash
echo "" >> cursor-progress.txt
echo "Session N: Implemented <feature description>" >> cursor-progress.txt
echo "- Tests: <test details>" >> cursor-progress.txt
echo "- Status: Passing" >> cursor-progress.txt
```

## Step 10: Mark Feature as Passing

Edit `feature_list.json`:
- Change ONLY the `"passes"` field from `false` to `true` for the feature you completed
- Keep everything else EXACTLY the same

**DO NOT:**
- ❌ Remove features from the list
- ❌ Edit feature descriptions or steps
- ❌ Add new features
- ❌ Change the order of features

**DO:**
- ✅ Change `"passes": false` to `"passes": true` for completed feature only

---

## Quality Standards

- Write tests BEFORE implementation (TDD)
- Aim for 80%+ test coverage
- No secrets or API keys in code
- No console.log/print statements in production code
- Follow existing code patterns
- Proper error handling
- Clear variable names

## When You're Done

After updating `feature_list.json` and `cursor-progress.txt`, your session is complete.

The next coding session will:
1. Read your progress notes
2. Pick the next feature
3. Continue the incremental development

**One feature at a time. Make it work. Move on.**

