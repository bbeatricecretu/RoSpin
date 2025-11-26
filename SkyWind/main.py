import json

from analysis.core.entities import Point, Region, region_to_geojson

region = Region(center = Point(46.7712, 23.6236))
region.generate_corners(side_km=20)
region.generate_grid(n=10)
geojson_data = region_to_geojson(region)
#save

with open ("region_zones.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson_data, f, indent = 2)

print("✅ region_zones.geojson generated successfully.")


