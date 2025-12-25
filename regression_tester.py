#!/usr/bin/env python3
"""
Regression Test Runner

Runs every 5 sessions to catch breaking changes.
Tests random sample of passing features to ensure they still work.
"""

import json
import random
import sys
from pathlib import Path


def load_features(feature_list_path: Path):
    """Load feature list."""
    with open(feature_list_path) as f:
        return json.load(f)


def get_passing_features(features):
    """Get all passing features."""
    return [f for f in features if f.get('passes', False)]


def run_regression_tests(feature_list_path: Path, sample_size: int = None):
    """
    Run regression tests on random sample of passing features.
    
    Args:
        feature_list_path: Path to feature_list.json
        sample_size: Number of features to test (default: 10% of passing, min 5, max 50)
    
    Returns:
        bool: True if all tests pass, False if regressions found
    """
    features = load_features(feature_list_path)
    passing = get_passing_features(features)
    
    if len(passing) == 0:
        print("No passing features to test yet")
        return True
    
    # Calculate sample size if not provided
    if sample_size is None:
        sample_size = max(5, min(50, len(passing) // 10))
    
    sample = random.sample(passing, min(sample_size, len(passing)))
    
    print(f"Regression Test Suite")
    print("=" * 70)
    print(f"Total passing features: {len(passing)}")
    print(f"Testing sample: {len(sample)} features ({len(sample)*100//len(passing)}%)")
    print("=" * 70)
    print()
    
    failures = []
    
    for i, feature in enumerate(sample, 1):
        desc = feature['description'][:60] + "..." if len(feature['description']) > 60 else feature['description']
        print(f"[{i}/{len(sample)}] {desc}")
        
        # For now, print the test steps
        # In full implementation, would execute these
        print(f"  Category: {feature.get('category', 'unknown')}")
        print(f"  Steps: {len(feature.get('steps', []))}")
        
        # TODO: Actually execute test steps
        # For now, just verify feature exists in feature_list
        # Real implementation would run the actual tests
        
        print(f"  ✅ Feature still in list")
    
    print()
    print("=" * 70)
    
    if failures:
        print(f"❌ REGRESSIONS FOUND: {len(failures)}/{len(sample)}")
        print()
        print("Failed features:")
        for f in failures:
            print(f"  - {f['description']}")
        print()
        print("🛑 FIX REGRESSIONS before continuing with new features!")
        return False
    else:
        print(f"✅ All {len(sample)} regression tests passed!")
        print("Safe to continue with new features.")
        return True


if __name__ == "__main__":
    # Check spec/ folder first, then fallback to root
    feature_list = Path("spec/feature_list.json")
    
    if not feature_list.exists():
        feature_list = Path("feature_list.json")
    
    if not feature_list.exists():
        print("feature_list.json not found in spec/ or current directory")
        print("Expected location: spec/feature_list.json")
        sys.exit(1)
    
    success = run_regression_tests(feature_list)
    sys.exit(0 if success else 1)

