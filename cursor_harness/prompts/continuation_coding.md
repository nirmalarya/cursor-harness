# Continuation Coding - For Large Existing Projects

You are continuing work on a project with MANY features (100+).

**This is a FRESH context window** - you have no memory of previous sessions.

---

## Step 1: Quick Orientation (Don't Read Everything!)

```bash
pwd
git log --oneline -10
tail -20 cursor-progress.txt
```

**CRITICAL: Do NOT read the entire feature_list.json!**
It's too large. Use Python to get summary instead:

```bash
python3 << 'EOF'
import json
with open('feature_list.json') as f:
    features = json.load(f)
total = len(features)
passing = sum(1 for f in features if f.get('passes') or f.get('completed'))
remaining = total - passing
print(f"Progress: {passing}/{total} ({passing/total*100:.1f}%)")
print(f"Remaining: {remaining} features")

# Find next feature to implement
for i, f in enumerate(features):
    if not (f.get('passes') or f.get('completed')):
        print(f"\nNext feature #{i}:")
        print(f"  {f.get('description', '')[:100]}")
        break
EOF
```

## Step 2: Check Completion

If all features are passing/completed, STOP - project is done.

## Step 3: Get Next Feature Details

Use Python to extract ONLY the next feature (not the whole list):

```bash
python3 << 'EOF'
import json
with open('feature_list.json') as f:
    features = json.load(f)

for i, f in enumerate(features):
    if not (f.get('passes') or f.get('completed')):
        print(f"Feature {i}: {f.get('description', '')}")
        print(f"Steps: {f.get('steps', [])}")
        
        # Save just this feature to work on
        with open('.next_feature.json', 'w') as out:
            json.dump({'index': i, 'feature': f}, out, indent=2)
        break
EOF

cat .next_feature.json
```

## Step 4: Start Server (If Applicable)

```bash
./init.sh || true
```

## Step 5: Implement the Feature

1. **Write tests first** (TDD)
2. **Implement** code
3. **Test manually**
4. **Verify end-to-end**

## Step 6: Commit

```bash
git add .
git commit -m "feat: implement feature #N"
```

## Step 7: Update Progress

```bash
echo "Session: Implemented feature #N - <description>" >> cursor-progress.txt
```

## Step 8: Mark Feature Complete

Use Python to update ONLY this feature (don't read whole file):

```bash
python3 << 'EOF'
import json

# Load just the index
with open('.next_feature.json') as f:
    data = json.load(f)
    index = data['index']

# Update just that feature
with open('feature_list.json') as f:
    features = json.load(f)

features[index]['passes'] = True

with open('feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"✅ Marked feature {index} as passing")
EOF

# Cleanup
rm .next_feature.json
```

---

**Key: Don't read huge feature_list.json! Use Python to extract what you need.**

