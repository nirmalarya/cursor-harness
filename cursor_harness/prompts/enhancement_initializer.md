# Enhancement Initializer - Session 1 (Brownfield)

You are setting up an enhancement workflow for an EXISTING project.

**Your job:** Prepare the environment for adding new features to existing codebase.

---

## Step 1: Understand Existing Project

```bash
# See what exists
ls -la

# Check git history
git log --oneline -20

# Look for README, docs
cat README.md || cat README || ls docs/
```

## Step 2: Read Enhancement Specification

Read the enhancement spec provided below. This describes features to add.

## Step 3: Create enhancement_list.json

Based on the spec, create a comprehensive list of enhancements:

```json
[
  {
    "category": "functional",
    "description": "Add dark mode toggle to settings panel",
    "steps": [
      "Navigate to settings",
      "Verify dark mode toggle exists",
      "Click toggle",
      "Verify theme changes to dark",
      "Reload page, verify preference persists"
    ],
    "completed": false
  }
]
```

**Format:**
- Root is array `[]`
- Each has: category, description, steps, completed
- ALL start with `"completed": false`
- Be comprehensive based on spec

## Step 4: Create cursor-progress.txt

```bash
echo "Session 1 (Enhancement Initializer): Environment set up for enhancements" > cursor-progress.txt
echo "- Analyzed existing codebase" >> cursor-progress.txt
echo "- Created enhancement_list.json with $(cat enhancement_list.json | python3 -c 'import json, sys; print(len(json.load(sys.stdin)))') enhancements" >> cursor-progress.txt
```

## Step 5: Initial Commit

```bash
git add enhancement_list.json cursor-progress.txt
git commit -m "chore: setup enhancement workflow"
```

---

**Your work is complete.** Future sessions will implement enhancements incrementally.

