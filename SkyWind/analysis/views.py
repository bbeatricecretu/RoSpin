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

def zones_geojson_detailed(request, region_id=1):
    """
    Încărcăm region_zones.geojson, apoi pentru fiecare feature (grid cell)
    completăm proprietăți din DB: de ex. avg_temperature, avg_wind_speed etc.
    Presupunem că feature.properties.id == Zone.zone_index în DB.
    """
    geo_path = Path(settings.BASE_DIR) / "region_zones.geojson"
    if not geo_path.exists():
        return HttpResponseNotFound("region_zones.geojson not found")

    data = json.loads(geo_path.read_text())

    # cache zonelor din DB într-un dict pentru lookup rapid
    zones = {}
    for z in Zone.objects.filter(region_id=region_id):
        zones[z.zone_index] = {
            "avg_temperature": getattr(z, "avg_temperature", None),
            "avg_wind_speed": getattr(z, "avg_wind_speed", None),
            "infrastructure_count": getattr(z, "infrastructure_count", None),  # dacă aveți așa ceva
            # adaugă aici alte câmpuri utile din modelul vostru
        }

    # atașează proprietăți la fiecare feature din geojson (doar dacă e poligon)
    for f in data.get("features", []):
        if f.get("geometry", {}).get("type") != "Polygon":
            continue
        fid = f.get("properties", {}).get("id") or f.get("id")
        det = zones.get(fid, {})
        # adaugăm/actualizăm properties
        props = f.setdefault("properties", {})
        props.update(det)

    return JsonResponse(data, safe=False)