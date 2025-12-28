# CRITICAL: Large Project - Use Python Scripts!

**STOP! This project has 100+ features. Do NOT read feature_list.json directly!**

---

## MANDATORY FIRST STEP: Get Next Feature with Python

**Run this FIRST (do NOT skip):**

```bash
python3 << 'SCRIPT'
import json

# Get summary WITHOUT reading whole file
with open('feature_list.json') as f:
    features = json.load(f)

total = len(features)
passing = sum(1 for f in features if f.get('passes', False))
remaining = total - passing

print(f"\n{'='*60}")
print(f"Progress: {passing}/{total} features ({passing/total*100:.1f}%)")
print(f"Remaining: {remaining} features")
print(f"{'='*60}\n")

# Find and extract ONLY next feature
for i, f in enumerate(features):
    if not f.get('passes', False):
        print(f"NEXT FEATURE (Index {i}):")
        print(f"Description: {f.get('description', '')}")
        print(f"Steps: {f.get('steps', [])}")
        
        # Save to temp file (don't keep in memory!)
        with open('.next_feature.json', 'w') as out:
            json.dump({
                'index': i,
                'description': f.get('description', ''),
                'steps': f.get('steps', []),
                'category': f.get('category', 'functional')
            }, out, indent=2)
        
        print(f"\nSaved to .next_feature.json")
        break

SCRIPT
```

**This extracts ONE feature without loading entire 7K line file into context!**

---

## Step 2: Check if Complete

If no feature found above, project is DONE. Stop working.

---

## Step 3: Read Feature Details

```bash
cat .next_feature.json
```

Now you have just ONE feature to implement.

---

## Step 4: Implement ONLY This Feature

1. Write tests for THIS feature
2. Implement THIS feature
3. Test THIS feature
4. Commit changes

**Do NOT:**
- ❌ Read entire feature_list.json
- ❌ Read other features
- ❌ Try to analyze whole project

**DO:**
- ✅ Implement just THIS feature
- ✅ Commit when done
- ✅ Mark complete (step below)

---

## Step 5: Mark Feature Complete

```bash
python3 << 'SCRIPT'
import json

# Get index
with open('.next_feature.json') as f:
    data = json.load(f)
    index = data['index']

# Update ONLY that feature
with open('feature_list.json') as f:
    features = json.load(f)

features[index]['passes'] = True

# Save back
with open('feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"✅ Marked feature {index} as passing")

SCRIPT

# Cleanup
rm .next_feature.json
```

---

## Step 6: Update Progress

```bash
# Read feature number
INDEX=$(cat .next_feature.json | python3 -c "import json, sys; print(json.load(sys.stdin)['index'])")
echo "Session N: Completed feature #$INDEX" >> cursor-progress.txt
```

---

## Step 7: Commit

```bash
git add .
git commit -m "feat: implement feature #INDEX"
```

**Done! Next session will pick up next feature.**

---

## REMEMBER:

**Use Python scripts to avoid reading huge files!**
**One feature at a time!**
**Keep it simple!**
