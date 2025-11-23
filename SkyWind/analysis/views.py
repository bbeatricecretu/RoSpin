from django.http import JsonResponse
from .models import Region, Zone
from .core.geometry import compute_region_corners, generate_zone_grid
import json

# ------------------------------------------------------------
# REGION DETAILS
# ------------------------------------------------------------
def get_region_details(request, region_id):
    try:
        r = Region.objects.select_related("center", "A", "B", "C", "D").get(pk=region_id)
    except Region.DoesNotExist:
        return JsonResponse({"error": "Region not found"}, status=404)

    data = {
        "id": r.id,
        "center": {"lat": r.center.lat, "lon": r.center.lon},
        "A": {"lat": r.A.lat, "lon": r.A.lon},
        "B": {"lat": r.B.lat, "lon": r.B.lon},
        "C": {"lat": r.C.lat, "lon": r.C.lon},
        "D": {"lat": r.D.lat, "lon": r.D.lon},

        "avg_temperature": r.avg_temperature,
        "wind_rose": r.wind_rose,
        "rating": r.rating,
        "avg_potential": r.avg_potential,
        "infrastructure_rating": r.infrastructure_rating,
        "index_average": r.index_average,
    }

    return JsonResponse(data, safe=False)

# ------------------------------------------------------------
# REGION ZONES
# ------------------------------------------------------------
def get_region_zones(request, region_id):
    zones = Zone.objects.filter(grid__region_id=region_id).select_related("A", "B", "C", "D")

    result = []
    for z in zones:
        result.append({
            "id": z.id,
            "zone_index": z.zone_index,

            "A": {"lat": z.A.lat, "lon": z.A.lon},
            "B": {"lat": z.B.lat, "lon": z.B.lon},
            "C": {"lat": z.C.lat, "lon": z.C.lon},
            "D": {"lat": z.D.lat, "lon": z.D.lon},

            "avg_wind_speed": z.avg_wind_speed,
            "min_alt": z.min_alt,
            "max_alt": z.max_alt,
            "roughness": z.roughness,
            "air_density": z.air_density,
            "power_avg": z.power_avg,
            "land_type": z.land_type,
            "potential": z.potential,
            "infrastructure_id": z.infrastructure.id if z.infrastructure else None,
        })

    return JsonResponse(result, safe=False)

# ------------------------------------------------------------
# SINGLE ZONE
# ------------------------------------------------------------
def get_zone_details(request, zone_id):
    try:
        z = Zone.objects.select_related("A", "B", "C", "D", "infrastructure").get(pk=zone_id)
    except Zone.DoesNotExist:
        return JsonResponse({"error": "Zone not found"}, status=404)

    return JsonResponse({
        "id": z.id,
        "zone_index": z.zone_index,

        "A": {"lat": z.A.lat, "lon": z.A.lon},
        "B": {"lat": z.B.lat, "lon": z.B.lon},
        "C": {"lat": z.C.lat, "lon": z.C.lon},
        "D": {"lat": z.D.lat, "lon": z.D.lon},

        "avg_wind_speed": z.avg_wind_speed,
        "min_alt": z.min_alt,
        "max_alt": z.max_alt,
        "roughness": z.roughness,
        "air_density": z.air_density,
        "power_avg": z.power_avg,
        "land_type": z.land_type,
        "potential": z.potential,
    })

# ------------------------------------------------------------
# COMPUTE REGION (NO DB)
# ------------------------------------------------------------
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def compute_region(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        lat = float(data["lat"])
        lon = float(data["lon"])
        side_km = float(data["side_km"])
        zones_per_edge = int(data["zones_per_edge"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid or missing fields"}, status=400)

    region_corners = compute_region_corners(lat, lon, side_km)

    zones = generate_zone_grid(
        region_corners["A"],
        region_corners["B"],
        region_corners["C"],
        region_corners["D"],
        zones_per_edge
    )

    flat_zones = []
    index = 0
    for row in zones:
        for z in row:
            flat_zones.append({
                "index": index,
                "A": {"lat": z["A"][0], "lon": z["A"][1]},
                "B": {"lat": z["B"][0], "lon": z["B"][1]},
                "C": {"lat": z["C"][0], "lon": z["C"][1]},
                "D": {"lat": z["D"][0], "lon": z["D"][1]},
            })
            index += 1

    return JsonResponse({
        "center": {"lat": lat, "lon": lon},
        "corners": {
            "A": {"lat": region_corners["A"][0], "lon": region_corners["A"][1]},
            "B": {"lat": region_corners["B"][0], "lon": region_corners["B"][1]},
            "C": {"lat": region_corners["C"][0], "lon": region_corners["C"][1]},
            "D": {"lat": region_corners["D"][0], "lon": region_corners["D"][1]},
        },
        "zones": flat_zones
    })
