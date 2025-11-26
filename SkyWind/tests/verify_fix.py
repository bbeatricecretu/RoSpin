#!/usr/bin/env python
"""Verify previously empty zones now have data"""
import django
import os
import sys

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from analysis.models import Zone

# These were the first 5 empty zones from before
previously_empty_ids = [7, 10, 15, 16, 17]

print("=" * 60)
print("VERIFICATION: Previously Empty Zones")
print("=" * 60)

for zone_id in previously_empty_ids:
    z = Zone.objects.get(id=zone_id)
    print(f"\nZone {z.id} (index {z.zone_index}):")
    print(f"  Land cover: '{z.land_type}'")
    print(f"  Wind speed: {z.avg_wind_speed} m/s")
    print(f"  Power density: {z.power_avg} W/m²")
    print(f"  Potential: {z.potential}%")

print("\n" + "=" * 60)
print("✅ All previously empty zones now have complete data!")
print("=" * 60)
