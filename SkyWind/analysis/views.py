from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .models import Point

import json
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotFound
from .models import Region

def zones_geojson(request):
    path = Path(settings.BASE_DIR) / "region_zones.geojson"
    if not path.exists():
        return HttpResponseNotFound("region_zones.geojson not found")
    data = json.loads(path.read_text())
    return JsonResponse(data, safe=False)

def region_center(request, region_id=1):
    try:
        r = Region.objects.select_related('center').get(pk=region_id)
        return JsonResponse({"lat": r.center.lat, "lon": r.center.lon})
    except Region.DoesNotExist:
        return JsonResponse({"error": "Region not found"}, status=404)

def points_list(request):
    points = Point.objects.all().values('id', 'lat', 'lon')
    return JsonResponse(list(points), safe=False)

import json
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotFound
from .models import Zone, Region

from django.http import JsonResponse
from .models import Region, Zone

def zones_geojson_detailed(request, region_id=1):
    """
    Generate GeoJSON for all zones of a region directly from DB.
    Build geometry from the zone's corner points A, B, C, D.
    """

    try:
        region = Region.objects.get(pk=region_id)
    except Region.DoesNotExist:
        return JsonResponse({"error": "Region not found"}, status=404)

    zones = Zone.objects.filter(region=region)

    features = []

    for z in zones:
        # Build polygon coordinates from A, B, C, D points
        polygon_coords = [[
            [z.A.lon, z.A.lat],
            [z.B.lon, z.B.lat],
            [z.C.lon, z.C.lat],
            [z.D.lon, z.D.lat],
            [z.A.lon, z.A.lat],  # close polygon
        ]]

        features.append({
            "type": "Feature",
            "properties": {
                "id": z.id,
                "zone_index": z.zone_index,
                "avg_wind_speed": z.avg_wind_speed,
                "min_alt": z.min_alt,
                "max_alt": z.max_alt,
                "roughness": z.roughness,
                "air_density": z.air_density,
                "power_avg": z.power_avg,
                "land_type": z.land_type,
                "potential": z.potential,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": polygon_coords
            }
        })

    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    })

