# Enhancement Continuation - For Large Enhancement Lists

You are adding enhancements to a project with MANY enhancements (>50).

**This is a FRESH context window** - you have no memory of previous sessions.

---

## Step 1: Quick Orientation (Don't Read Everything!)

```bash
pwd
git log --oneline -10
tail -20 cursor-progress.txt
```

**CRITICAL: Do NOT read the entire enhancement_list.json!**

Use Python to get summary:

```bash
python3 << 'EOF'
import json
with open('enhancement_list.json') as f:
    enhancements = json.load(f)
total = len(enhancements)
completed = sum(1 for e in enhancements if e.get('completed'))
remaining = total - completed
print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%)")
print(f"Remaining: {remaining} enhancements")

# Find next enhancement
for i, e in enumerate(enhancements):
    if not e.get('completed'):
        print(f"\nNext enhancement #{i}:")
        print(f"  {e.get('description', '')[:100]}")
        break
EOF
```

## Step 2: Check Completion

If all completed, STOP - enhancements are done.

## Step 3: Get Next Enhancement

```bash
python3 << 'EOF'
import json
with open('enhancement_list.json') as f:
    enhancements = json.load(f)

for i, e in enumerate(enhancements):
    if not e.get('completed'):
        print(f"Enhancement {i}: {e.get('description', '')}")
        print(f"Steps: {e.get('steps', [])}")
        
        with open('.next_enhancement.json', 'w') as out:
            json.dump({'index': i, 'enhancement': e}, out, indent=2)
        break
EOF

cat .next_enhancement.json
```

## Step 4: Implement

1. Write tests
2. Implement (integrate with existing code)
3. Verify no regressions

**Hooks will auto-run tests and linters!**

## Step 5: Commit

```bash
git add .
git commit -m "feat: <enhancement>"
```

## Step 6: Update Progress

```bash
echo "Session: Implemented enhancement #N" >> cursor-progress.txt
```

## Step 7: Mark Complete

```bash
python3 << 'EOF'
import json

with open('.next_enhancement.json') as f:
    data = json.load(f)
    index = data['index']

with open('enhancement_list.json') as f:
    enhancements = json.load(f)

enhancements[index]['completed'] = True

with open('enhancement_list.json', 'w') as f:
    json.dump(enhancements, f, indent=2)

print(f"✅ Marked enhancement {index} complete")
EOF

rm .next_enhancement.json
```

---

**Don't read huge files! Use Python to extract what you need.**

