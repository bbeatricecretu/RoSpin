#!/usr/bin/env python
"""Diagnose land cover fetching issue"""
import django
import os
import sys

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import ee
from analysis.models import Zone
from analysis.core.gee_data import get_landcover_image, WORLD_COVER_CLASSES

# Test with one empty zone and one filled zone
empty_zone = Zone.objects.filter(land_type='').first()
filled_zone = Zone.objects.exclude(land_type='').first()

print("=" * 60)
print("TESTING EARTH ENGINE LAND COVER FETCHING")
print("=" * 60)

def test_zone(z, label):
    print(f"\n{label}")
    print(f"Zone {z.id} (index {z.zone_index})")
    print(f"Current land_type in DB: '{z.land_type}'")
    
    # Build polygon
    poly = [
        [z.A.lon, z.A.lat],
        [z.B.lon, z.B.lat],
        [z.C.lon, z.C.lat],
        [z.D.lon, z.D.lat],
        [z.A.lon, z.A.lat],
    ]
    
    print(f"Polygon coords: {poly[:2]}...")
    
    # Create feature
    feature = ee.Feature(
        ee.Geometry.Polygon([poly]),
        {"zone_id": z.id}
    )
    
    fc = ee.FeatureCollection([feature])
    
    # Get land cover image
    img = get_landcover_image()
    
    # Try frequency histogram
    print("\n  Testing frequencyHistogram reducer...")
    try:
        result = img.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.frequencyHistogram(),
            scale=10
        ).getInfo()
        
        props = result['features'][0]['properties']
        hist = props.get('histogram')
        
        print(f"  ✓ Request succeeded")
        print(f"  Histogram: {hist}")
        
        if hist:
            print(f"  Histogram type: {type(hist)}")
            print(f"  Histogram keys: {list(hist.keys())}")
            max_count = max(hist.values())
            dominant = [int(k) for k, v in hist.items() if v == max_count]
            labels = [WORLD_COVER_CLASSES.get(c, f"class_{c}") for c in dominant]
            print(f"  Dominant classes: {', '.join(labels)}")
        else:
            print(f"  ⚠ Histogram is None or empty!")
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    # Also try mode reducer as comparison
    print("\n  Testing mode reducer (for comparison)...")
    try:
        result = img.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.mode(),
            scale=10
        ).getInfo()
        
        props = result['features'][0]['properties']
        mode_val = props.get('mode')
        
        print(f"  ✓ Mode request succeeded")
        print(f"  Mode value: {mode_val}")
        
        if mode_val:
            label = WORLD_COVER_CLASSES.get(int(mode_val), f"class_{mode_val}")
            print(f"  Mode label: {label}")
        else:
            print(f"  ⚠ Mode is None!")
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

# Test both zones
test_zone(empty_zone, "=== EMPTY ZONE TEST ===")
test_zone(filled_zone, "=== FILLED ZONE TEST ===")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
