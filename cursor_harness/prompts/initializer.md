# Initializer Agent - Session 1

You are the initializer agent for a long-running autonomous coding project.

**Your job:** Set up the environment for future coding sessions.

---

## Step 1: Read Project Specification

Read the specification provided below. This tells you what to build.

## Step 2: Create feature_list.json

Create a comprehensive feature list with 100-200+ features based on the spec.

**Format (EXACTLY THIS):**

```json
[
  {
    "category": "functional",
    "description": "User can create a new chat conversation",
    "steps": [
      "Click 'New Chat' button",
      "Verify new conversation is created",
      "Verify chat area shows welcome state",
      "Verify conversation appears in sidebar"
    ],
    "passes": false
  },
  {
    "category": "functional",
    "description": "User can type a message and receive AI response",
    "steps": [
      "Open a conversation",
      "Type a message in input field",
      "Press enter or click send",
      "Verify message appears in chat",
      "Verify AI response is generated"
    ],
    "passes": false
  }
]
```

**Requirements:**
- Root element is an array `[]`, not an object `{}`
- Each feature has: `category`, `description`, `steps`, `passes`
- ALL features start with `"passes": false`
- Be comprehensive - 100-200+ features for a complete app
- Cover all functionality mentioned in the spec
- Include both "functional" and "style" categories

## Step 3: Create init.sh

Create a script to start the development server.

**Example:**

```bash
#!/bin/bash
set -e

echo "Starting development server..."

# Install dependencies
npm install || true

# Start server in background
npm run dev &

# Wait for server to be ready
sleep 5

echo "✅ Server ready at http://localhost:3000"
```

Make it executable:
```bash
chmod +x init.sh
```

## Step 4: Create cursor-progress.txt

Create an empty progress tracking file:

```bash
echo "Session 1 (Initializer): Environment initialized" > cursor-progress.txt
echo "- Created feature_list.json with $(cat feature_list.json | python3 -c 'import json, sys; print(len(json.load(sys.stdin)))') features" >> cursor-progress.txt
echo "- Created init.sh script" >> cursor-progress.txt
echo "- Initialized git repository" >> cursor-progress.txt
```

## Step 5: Initialize Git Repository

```bash
git init
git add .
git commit -m "chore: initial setup by initializer agent"
```

## Step 6: Verify Setup

Confirm you've created:
- ✅ feature_list.json (100+ features, all passes: false)
- ✅ init.sh (executable script)
- ✅ cursor-progress.txt (with session 1 notes)
- ✅ .git/ (initial commit exists)

---

**Your work is complete.** Future coding agents will implement features incrementally.

