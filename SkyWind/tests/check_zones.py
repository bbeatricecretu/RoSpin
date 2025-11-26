#!/usr/bin/env python
"""Temporary script to check zone land cover status"""
import django
import os
import sys

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from analysis.models import Zone

# Get statistics
empty = Zone.objects.filter(land_type='')
total = Zone.objects.count()

print(f'Total zones: {total}')
print(f'Empty land_type: {empty.count()}')

if total > 0:
    print(f'Percentage: {empty.count()/total*100:.1f}%')
    
print('\n=== First 5 empty zones ===')
for z in empty[:5]:
    print(f'Zone {z.id} (index {z.zone_index}):')
    print(f'  A=({z.A.lat:.5f}, {z.A.lon:.5f})')
    print(f'  B=({z.B.lat:.5f}, {z.B.lon:.5f})')
    print(f'  C=({z.C.lat:.5f}, {z.C.lon:.5f})')
    print(f'  D=({z.D.lat:.5f}, {z.D.lon:.5f})')
    print()

print('\n=== Sample zones WITH land cover ===')
filled = Zone.objects.exclude(land_type='')[:5]
for z in filled:
    print(f'Zone {z.id}: land_type="{z.land_type}"')
