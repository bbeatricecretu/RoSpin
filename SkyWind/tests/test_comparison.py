#!/usr/bin/env python
"""Test the exact comparison issue"""

# Simulate the histogram data
hist = {
    '10': 7628.270588235291,
    '20': 1.0,
    '30': 25049.27843137277,
    '40': 22319.27843137262,
    '50': 3549.329411764708,
    '60': 72.0
}

print("Original histogram:")
for k, v in hist.items():
    print(f"  {k}: {v}")

print(f"\nmax(hist.values()) = {max(hist.values())}")
max_count = max(hist.values())

print(f"\nChecking equality:")
for k, v in hist.items():
    equal = (v == max_count)
    print(f"  {k}: {v} == {max_count} ? {equal}")

dominant_classes = [int(k) for k, v in hist.items() if v == max_count]
print(f"\nDominant classes: {dominant_classes}")

# The fix: compare with a small epsilon
print("\n" + "="*60)
print("TESTING FIXED VERSION:")
print("="*60)

# Find classes within 0.01 of max (effectively equal)
epsilon = 0.01
dominant_fixed = [int(k) for k, v in hist.items() if abs(v - max_count) < epsilon]
print(f"Dominant classes (with epsilon): {dominant_fixed}")
