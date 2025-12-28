# Backlog Initializer - Session 1 (Azure DevOps)

You are setting up a backlog workflow for processing Azure DevOps work items.

**Your job:** Prepare environment for processing PBIs from Azure DevOps.

---

## Step 1: Understand Existing Project

```bash
ls -la
git log --oneline -20
cat README.md || ls docs/
```

## Step 2: Read Backlog State

The harness has already fetched PBIs from Azure DevOps into `.cursor/backlog-state.json`.

Read this file:
```bash
cat .cursor/backlog-state.json | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"{len(data['pbis'])} PBIs fetched\")"
```

## Step 3: Convert to feature_list.json

Convert PBIs to feature_list.json format for consistent workflow:

```bash
cat .cursor/backlog-state.json | python3 << 'EOF'
import json, sys

backlog = json.load(sys.stdin)
features = []

for pbi in backlog['pbis']:
    features.append({
        "category": "pbi",
        "pbi_id": pbi['id'],
        "description": f"{pbi['title']} - {pbi['description']}",
        "steps": pbi['acceptance_criteria'].split('\n') if pbi.get('acceptance_criteria') else [],
        "passes": False
    })

with open('feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)
    
print(f"Converted {len(features)} PBIs to feature_list.json")
EOF
```

## Step 4: Create cursor-progress.txt

```bash
echo "Session 1 (Backlog Initializer): Backlog workflow initialized" > cursor-progress.txt
echo "- Loaded $(cat .cursor/backlog-state.json | python3 -c 'import json, sys; print(len(json.load(sys.stdin)[\"pbis\"]))'  ) PBIs from Azure DevOps" >> cursor-progress.txt
echo "- Created feature_list.json" >> cursor-progress.txt
```

## Step 5: Initial Commit

```bash
git add feature_list.json cursor-progress.txt
git commit -m "chore: setup backlog workflow"
```

---

**Your work is complete.** Future sessions will process PBIs incrementally.

