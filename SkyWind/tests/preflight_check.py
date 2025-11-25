#!/usr/bin/env python
"""
Pre-flight check before running fetch_gee_data
Verifies database is properly set up
"""
import django
import os
import sys

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from analysis.models import RegionGrid, Zone, Infrastructure, Region

print("=" * 70)
print("PRE-FLIGHT CHECK FOR fetch_gee_data")
print("=" * 70)

errors = []
warnings = []
success = []

# Check 1: Regions exist
print("\n1️⃣  Checking Regions...")
regions = Region.objects.all()
if not regions.exists():
    errors.append("❌ No regions found! Create a region first.")
else:
    success.append(f"✅ Found {regions.count()} region(s)")
    for r in regions:
        print(f"   • Region {r.id}: center at ({r.center.lat:.4f}, {r.center.lon:.4f})")

# Check 2: RegionGrids exist
print("\n2️⃣  Checking RegionGrids...")
grids = RegionGrid.objects.all()
if not grids.exists():
    errors.append("❌ No grids found! Run 'python manage.py generates_zones' first.")
else:
    success.append(f"✅ Found {grids.count()} grid(s)")
    for g in grids:
        print(f"   • Grid {g.id}: {g.zones_per_edge}×{g.zones_per_edge} for Region {g.region.id}")

# Check 3: Zones exist
print("\n3️⃣  Checking Zones...")
zones = Zone.objects.all()
if not zones.exists():
    errors.append("❌ No zones found! Run 'python manage.py generates_zones' first.")
else:
    success.append(f"✅ Found {zones.count()} zone(s)")
    
    # Check if zones have infrastructure
    zones_without_infra = Zone.objects.filter(infrastructure__isnull=True)
    if zones_without_infra.exists():
        warnings.append(f"⚠️  {zones_without_infra.count()} zones have no infrastructure (will be auto-created)")
    else:
        success.append(f"✅ All zones have infrastructure objects")

# Check 4: Infrastructure objects
print("\n4️⃣  Checking Infrastructure...")
infra = Infrastructure.objects.all()
if not infra.exists():
    warnings.append("⚠️  No infrastructure objects found (will be auto-created)")
else:
    success.append(f"✅ Found {infra.count()} infrastructure object(s)")

# Check 5: Earth Engine initialization
print("\n5️⃣  Checking Earth Engine...")
try:
    import ee
    ee.Initialize(project='rospin1')
    success.append("✅ Earth Engine initialized successfully")
except Exception as e:
    errors.append(f"❌ Earth Engine error: {e}")

# Check 6: Required packages
print("\n6️⃣  Checking Required Packages...")
required_packages = ['ee', 'requests', 'geopy']
for pkg in required_packages:
    try:
        __import__(pkg)
        success.append(f"✅ {pkg} installed")
    except ImportError:
        errors.append(f"❌ {pkg} not installed! Run: pip install {pkg}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if success:
    print("\n✅ PASSED:")
    for s in success:
        print(f"   {s}")

if warnings:
    print("\n⚠️  WARNINGS:")
    for w in warnings:
        print(f"   {w}")

if errors:
    print("\n❌ ERRORS:")
    for e in errors:
        print(f"   {e}")
    print("\n🛑 CANNOT PROCEED - Fix errors above first!")
    sys.exit(1)
else:
    print("\n" + "=" * 70)
    print("✅ ALL CHECKS PASSED - Ready to run fetch_gee_data!")
    print("=" * 70)
    print("\nRun:")
    print("  docker compose exec web python manage.py fetch_gee_data")
    print("\nThis will:")
    print("  1. Fetch temperature (region)")
    print("  2. Fetch wind speed & direction (zones)")
    print("  3. Fetch DEM data (zones)")
    print("  4. Fetch air density (zones)")
    print("  5. Fetch wind power density (zones)")
    print("  6. Fetch land cover (zones)")
    print("  7. Calculate potential scores (zones)")
    print("  8. Fetch infrastructure accessibility (zones) ⏱️  ~10-15 minutes")
    print("  9. Calculate region metrics")
    print("\n⏱️  Estimated time: 15-20 minutes for 100 zones")
    sys.exit(0)
