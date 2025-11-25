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
# COMPUTE REGION (WITH DB)
# ------------------------------------------------------------
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import Region, RegionGrid, Zone, Point, Infrastructure
from .core.geometry import compute_region_corners, generate_zone_grid
import json


# ----------------------------
# POINT HELPERS
# ----------------------------

def _get_or_reuse_point(lat, lon):
    """
    Get or create a point with rounding to avoid floating point issues.
    Used for all point creation (regions, grids, zones).
    """
    # Round to 9 decimal places (~1cm precision)
    lat_rounded = round(lat, 9)
    lon_rounded = round(lon, 9)
    p, _ = Point.objects.get_or_create(lat=lat_rounded, lon=lon_rounded)
    return p


# ----------------------------
# GEOMETRY MATCH CHECK
# ----------------------------

def _zones_match_expected(grid: RegionGrid) -> bool:
    """Compare existing zone geometry with expected geometry."""

    expected_corners = compute_region_corners(
        center_lat=grid.region.center.lat,
        center_lon=grid.region.center.lon,
        side_km=grid.side_km,
    )

    expected_grid = generate_zone_grid(
        A=expected_corners["A"],
        B=expected_corners["B"],
        C=expected_corners["C"],
        D=expected_corners["D"],
        n=grid.zones_per_edge,
    )

    zones = list(grid.zones.order_by("zone_index"))
    required = grid.zones_per_edge * grid.zones_per_edge
    if len(zones) != required:
        return False

    idx = 0
    tolerance = 1e-7  # Tolerance for floating point comparison
    for row in expected_grid:
        for cell in row:
            z = zones[idx]
            if (
                    abs(z.A.lat - cell["A"][0]) > tolerance or
                    abs(z.A.lon - cell["A"][1]) > tolerance or
                    abs(z.B.lat - cell["B"][0]) > tolerance or
                    abs(z.B.lon - cell["B"][1]) > tolerance or
                    abs(z.C.lat - cell["C"][0]) > tolerance or
                    abs(z.C.lon - cell["C"][1]) > tolerance or
                    abs(z.D.lat - cell["D"][0]) > tolerance or
                    abs(z.D.lon - cell["D"][1]) > tolerance
            ):
                return False
            idx += 1

    return True


# ----------------------------
# ZONE GENERATION
# ----------------------------

def _generate_zones_for_grid(grid: RegionGrid):
    """Generate NEW zones using ALREADY computed region/grid corners."""

    infra, _ = Infrastructure.objects.get_or_create(index=1)

    A = grid.A
    B = grid.B
    C = grid.C
    D = grid.D

    zone_grid = generate_zone_grid(
        A=(A.lat, A.lon),
        B=(B.lat, B.lon),
        C=(C.lat, C.lon),
        D=(D.lat, D.lon),
        n=grid.zones_per_edge,
    )

    created = []
    zone_index = 1

    for row in zone_grid:
        for cell in row:
            A_z = _get_or_reuse_point(*cell["A"])
            B_z = _get_or_reuse_point(*cell["B"])
            C_z = _get_or_reuse_point(*cell["C"])
            D_z = _get_or_reuse_point(*cell["D"])

            z = Zone.objects.create(
                grid=grid,
                A=A_z, B=B_z, C=C_z, D=D_z,
                infrastructure=infra,
                zone_index=zone_index,
            )
            created.append(z)
            zone_index += 1

    return created


def _delete_grid_zones(grid: RegionGrid):
    """
    Delete zones only - DO NOT delete points.
    Points are shared resources that will be reused via get_or_create.
    This prevents conflicts when regions overlap at the same center.
    """
    grid.zones.all().delete()


# ----------------------------
# MAIN ENDPOINT
# ----------------------------

@csrf_exempt
def compute_region(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        lat = float(data["lat"])
        lon = float(data["lon"])
        side_km = float(data["side_km"])
        zpe = int(data["zones_per_edge"])
    except Exception:
        return JsonResponse({"error": "Invalid fields"}, status=400)

    with transaction.atomic():

        # 1) CENTER POINT
        center_pt = _get_or_reuse_point(lat, lon)

        # 2) COMPUTE corners for this specific side_km
        corners = compute_region_corners(lat, lon, side_km)

        A = _get_or_reuse_point(*corners["A"])
        B = _get_or_reuse_point(*corners["B"])
        C = _get_or_reuse_point(*corners["C"])
        D = _get_or_reuse_point(*corners["D"])

        # 3) REGION SELECTION LOGIC
        # Check if a region exists with this center AND this side_km
        existing_region = None

        # Get all regions at this center
        regions_at_center = Region.objects.filter(center=center_pt).prefetch_related('grids')

        for reg in regions_at_center:
            # Check if this region has a grid with matching side_km
            if reg.grids.filter(side_km=side_km).exists():
                existing_region = reg
                break

        if existing_region:
            # Reuse existing region with same center + side_km
            region = existing_region
        else:
            # Create NEW region (different side_km or new location)
            region = Region.objects.create(
                center=center_pt,
                A=A, B=B, C=C, D=D
            )

        # Update region corners
        region.A = A
        region.B = B
        region.C = C
        region.D = D
        region.save()

        # 4) REGION GRID (get existing or create new)
        grid, grid_created = RegionGrid.objects.get_or_create(
            region=region,
            side_km=side_km,
            zones_per_edge=zpe
        )

        # Update grid corners
        grid.A = A
        grid.B = B
        grid.C = C
        grid.D = D
        grid.save()

        # 5) ZONES – regenerate only when needed
        need_regeneration = (
                not grid.zones.exists() or
                not _zones_match_expected(grid)
        )

        if need_regeneration:
            # Delete old zones before creating new ones
            _delete_grid_zones(grid)
            zones = _generate_zones_for_grid(grid)
        else:
            zones = list(grid.zones.all())

    # ----------------------------
    # RESPONSE
    # ----------------------------

    resp_corners = {
        "A": {"lat": region.A.lat, "lon": region.A.lon},
        "B": {"lat": region.B.lat, "lon": region.B.lon},
        "C": {"lat": region.C.lat, "lon": region.C.lon},
        "D": {"lat": region.D.lat, "lon": region.D.lon},
    }

    resp_zones = [{
        "id": z.id,
        "index": z.zone_index,
        "A": {"lat": z.A.lat, "lon": z.A.lon},
        "B": {"lat": z.B.lat, "lon": z.B.lon},
        "C": {"lat": z.C.lat, "lon": z.C.lon},
        "D": {"lat": z.D.lat, "lon": z.D.lon},
    } for z in zones]

    return JsonResponse({
        "region_id": region.id,
        "center": {"lat": lat, "lon": lon},
        "corners": resp_corners,
        "zones": resp_zones,
    })
