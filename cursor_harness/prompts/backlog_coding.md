# Backlog Coding - Process PBIs (Azure DevOps)

You are processing Azure DevOps work items (PBIs) incrementally.

**This is a FRESH context window** - you have no memory of previous sessions.

---

## Step 1: Get Your Bearings

```bash
pwd
git log --oneline -20
cat cursor-progress.txt
cat feature_list.json | head -50
```

## Step 2: Check Completion

```bash
total=$(cat feature_list.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))")
passing=$(cat feature_list.json | python3 -c "import json, sys; print(len([f for f in json.load(sys.stdin) if f.get('passes')]))")
echo "$passing/$total PBIs complete"
```

If all passing, STOP - backlog is complete.

## Step 3: Pick ONE PBI

Find first PBI where passes: false.
Work on ONLY this PBI.

```bash
cat feature_list.json | python3 -c "
import json, sys
features = json.load(sys.stdin)
for i, f in enumerate(features):
    if not f.get('passes'):
        print(f'PBI {i}: {f.get(\"pbi_id\", \"\")} - {f[\"description\"]}')
        print(f'Steps: {f.get(\"steps\", [])}')
        break
"
```

## Step 4: Implement PBI

1. **Write tests first** - Based on acceptance criteria
2. **Implement** - Add the feature/fix
3. **Test manually** - Verify works end-to-end
4. **Run all tests** - Ensure no regressions

## Step 5: Commit

```bash
git add .
git commit -m "[{pbi_id}] feat: <description>"
```

Use PBI ID in commit message for traceability.

## Step 6: Update Progress

```bash
echo "Session N: Completed PBI {pbi_id}" >> cursor-progress.txt
```

## Step 7: Mark PBI Complete

Edit `feature_list.json` - change passes: false to passes: true for this PBI.

## Step 8: Update Azure DevOps (If Possible)

If you have access to Azure DevOps MCP tools, add a comment to the work item:

```
Completed: {pbi_title}
- Tests added
- Implementation complete
- All tests passing
```

---

**One PBI at a time. Verify quality. Move on.**

