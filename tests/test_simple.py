"""
Simple test to validate cursor-harness v3.0 core loop.

Tests the basic workflow:
1. Initialize project
2. Load features
3. Process features
4. Mark complete
"""

import json
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import CursorHarness, WorkItem


def test_greenfield_simple():
    """Test greenfield mode with simple feature list."""
    
    print("\n" + "="*60)
    print("TEST: Simple Greenfield Mode")
    print("="*60)
    
    # Create test project
    test_dir = Path("/tmp/cursor-harness-test-simple")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)
    
    # Create simple feature list
    features = [
        {
            "id": "1",
            "title": "Create README",
            "description": "Create a README.md file for the project",
            "passing": False
        },
        {
            "id": "2",
            "title": "Add .gitignore",
            "description": "Create a .gitignore file",
            "passing": False
        }
    ]
    
    feature_list = test_dir / "feature_list.json"
    with open(feature_list, 'w') as f:
        json.dump(features, f, indent=2)
    
    print(f"\n✅ Test project created: {test_dir}")
    print(f"✅ Feature list: {len(features)} features")
    
    # Create harness
    harness = CursorHarness(
        project_dir=test_dir,
        mode="greenfield",
        timeout_minutes=5  # Short timeout for testing
    )
    
    # Test setup
    print("\n" + "-"*60)
    print("Testing setup...")
    print("-"*60)
    harness._setup()
    
    # Verify git initialized
    assert (test_dir / ".git").exists(), "Git should be initialized"
    print("✅ Git initialized")
    
    # Verify mode adapter loaded
    assert harness.mode_adapter is not None, "Mode adapter should be loaded"
    print("✅ Mode adapter loaded")
    
    # Test getting work
    print("\n" + "-"*60)
    print("Testing work item retrieval...")
    print("-"*60)
    
    work1 = harness._get_next_work()
    assert work1 is not None, "Should get first work item"
    assert work1.id == "1", "First work item should be ID 1"
    print(f"✅ Got work item: {work1.title}")
    
    # Test marking complete
    print("\n" + "-"*60)
    print("Testing completion...")
    print("-"*60)
    
    harness._mark_complete(work1)
    
    # Verify feature marked as passing
    with open(feature_list) as f:
        updated_features = json.load(f)
    
    assert updated_features[0]["passing"] == True, "Feature 1 should be passing"
    print("✅ Feature 1 marked as passing")
    
    # Get next work
    work2 = harness._get_next_work()
    assert work2 is not None, "Should get second work item"
    assert work2.id == "2", "Second work item should be ID 2"
    print(f"✅ Got work item: {work2.title}")
    
    # Mark second complete
    harness._mark_complete(work2)
    
    # Verify complete
    assert harness._is_complete(), "Project should be complete"
    print("✅ Project marked as complete")
    
    # Verify no more work
    work3 = harness._get_next_work()
    assert work3 is None, "Should be no more work"
    print("✅ No more work items")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\ncore.py loop is working correctly! 🎉")
    print("\nNext steps:")
    print("1. ✅ Core loop works")
    print("2. 🔧 Add cursor-agent execution")
    print("3. 🔧 Add validation")
    print("4. 🔧 Add other modes")


if __name__ == "__main__":
    test_greenfield_simple()

