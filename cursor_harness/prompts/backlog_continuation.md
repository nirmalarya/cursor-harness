# Backlog Continuation - For Large PBI Lists

You are processing Azure DevOps PBIs with MANY work items (>50).

**This is a FRESH context window** - you have no memory of previous sessions.

---

## Step 1: Quick Orientation (Don't Read Everything!)

```bash
pwd
git log --oneline -10
tail -20 cursor-progress.txt
```

**CRITICAL: Do NOT read the entire feature_list.json!**

Use Python to get summary:

```bash
python3 << 'EOF'
import json
with open('feature_list.json') as f:
    features = json.load(f)
total = len(features)
passing = sum(1 for f in features if f.get('passes'))
remaining = total - passing
print(f"Progress: {passing}/{total} PBIs ({passing/total*100:.1f}%)")
print(f"Remaining: {remaining} PBIs")

# Find next PBI
for i, f in enumerate(features):
    if not f.get('passes'):
        pbi_id = f.get('pbi_id', 'unknown')
        print(f"\nNext PBI #{i}: {pbi_id}")
        print(f"  {f.get('description', '')[:100]}")
        break
EOF
```

## Step 2: Check Completion

If all passing, STOP - backlog is complete.

## Step 3: Get Next PBI

```bash
python3 << 'EOF'
import json
with open('feature_list.json') as f:
    features = json.load(f)

for i, f in enumerate(features):
    if not f.get('passes'):
        print(f"PBI {i}: {f.get('pbi_id', '')} - {f.get('description', '')}")
        print(f"Steps: {f.get('steps', [])}")
        
        with open('.next_pbi.json', 'w') as out:
            json.dump({'index': i, 'pbi': f}, out, indent=2)
        break
EOF

cat .next_pbi.json
```

## Step 4: Implement PBI

1. Write tests (TDD)
2. Implement feature
3. Verify end-to-end

**Hooks will auto-run tests and build checks!**

## Step 5: Commit

```bash
git add .
git commit -m "[{pbi_id}] feat: <description>"
```

## Step 6: Update Progress

```bash
echo "Session: Completed PBI #{pbi_id}" >> cursor-progress.txt
```

## Step 7: Mark PBI Complete

```bash
python3 << 'EOF'
import json

with open('.next_pbi.json') as f:
    data = json.load(f)
    index = data['index']

with open('feature_list.json') as f:
    features = json.load(f)

features[index]['passes'] = True

with open('feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"✅ Marked PBI {index} as passing")
EOF

rm .next_pbi.json
```

---

**Use Python to avoid reading huge files! Hooks handle validation!**

