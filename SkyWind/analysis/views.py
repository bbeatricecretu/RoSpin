from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Region, RegionGrid, Zone, Point, Infrastructure, WindTurbineType
from analysis.core.gee_service import compute_gee_for_grid
from .core.geometry import compute_region_corners, generate_zone_grid
import json

# ------------------------------------------------------------
# REGION DETAILS (AUTO-GEE IF NEEDED)
# ------------------------------------------------------------
def get_region_details(request, region_id):
    try:
        r = Region.objects.select_related("A", "B", "C", "D", "center").get(pk=region_id)
    except Region.DoesNotExist:
        return JsonResponse({"error": "Region not found"}, status=404)

    grid = r.grids.first()

    # Auto-fetch GEE ONLY if region has no data yet
    if grid and r.avg_temperature == 0:
        compute_gee_for_grid(grid)

    return JsonResponse({
        "id": r.id,

        # geometry
        "center": {"lat": r.center.lat, "lon": r.center.lon},
        "A": {"lat": r.A.lat, "lon": r.A.lon},
        "B": {"lat": r.B.lat, "lon": r.B.lon},
        "C": {"lat": r.C.lat, "lon": r.C.lon},
        "D": {"lat": r.D.lat, "lon": r.D.lon},

        # region metrics
        "avg_temperature": r.avg_temperature,
        "wind_rose": r.wind_rose,
        "rating": r.rating,
        "avg_potential": r.avg_potential,
        "infrastructure_rating": r.infrastructure_rating,
        "index_average": r.index_average,
        "max_potential_zone": r.max_potential.id if r.max_potential else None,
    })


def get_region_zones(request, region_id):
    zones = Zone.objects.filter(
        grid__region_id=region_id
    ).select_related("A", "B", "C", "D")

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
# ZONE DETAILS (AUTO-GEE IF NEEDED)
# ------------------------------------------------------------
def get_zone_details(request, zone_id):
    try:
        z = Zone.objects.select_related(
            "A", "B", "C", "D", "infrastructure", "grid", "grid__region"
        ).get(pk=zone_id)
    except Zone.DoesNotExist:
        return JsonResponse({"error": "Zone not found"}, status=404)

    # auto-GEE refresh if missing
    region = z.grid.region
    grid = z.grid

    if region.avg_temperature == 0 or z.avg_wind_speed == 0:
        compute_gee_for_grid(grid)

        # refresh object
        z = Zone.objects.select_related(
            "A", "B", "C", "D", "infrastructure", "grid", "grid__region"
        ).get(pk=zone_id)

    return JsonResponse({

        "id": z.id,
        "zone_index": z.zone_index,
        "region_id": z.grid.region.id,
        "grid_id": z.grid.id,

        # geometry
        "A": {"lat": z.A.lat, "lon": z.A.lon},
        "B": {"lat": z.B.lat, "lon": z.B.lon},
        "C": {"lat": z.C.lat, "lon": z.C.lon},
        "D": {"lat": z.D.lat, "lon": z.D.lon},

        # wind
        "avg_wind_speed": z.avg_wind_speed,
        "wind_direction": z.wind_direction,

        # terrain
        "min_alt": z.min_alt,
        "max_alt": z.max_alt,
        "roughness": z.roughness,

        # air + power
        "air_density": z.air_density,
        "power_avg": z.power_avg,

        # classification
        "land_type": z.land_type,
        "potential": z.potential,

        # infra
        "infrastructure": {
            "index": z.infrastructure.index,
            "km_jud": z.infrastructure.km_jud,
            "km_nat": z.infrastructure.km_nat,
            "km_euro": z.infrastructure.km_euro,
            "km_auto": z.infrastructure.km_auto,
        }
    })


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
# MAIN ENDPOINT: COMPUTE REGION
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


# ------------------------------------------------------------
# NEW: REGION ZONE POWERS (TURBINE-SPECIFIC)
# ------------------------------------------------------------

def get_region_zone_powers(request, region_id):
    """
    Returns all zones of a region with coordinates and achievable power (kW)
    for a given turbine type.

    Query params:
        turbine_id: ID of WindTurbineType
    """
    turbine_id = request.GET.get("turbine_id")
    if not turbine_id:
        return JsonResponse({"error": "turbine_id is required"}, status=400)

    try:
        region = Region.objects.get(pk=region_id)
    except Region.DoesNotExist:
        return JsonResponse({"error": "Region not found"}, status=404)

    try:
        turbine = WindTurbineType.objects.get(pk=turbine_id)
    except WindTurbineType.DoesNotExist:
        return JsonResponse({"error": "Turbine type not found"}, status=404)

    zone_powers = region.zone_power_for_turbines(turbine)

    result = []
    for item in zone_powers:
        z = item["zone"]
        power_kw = item["power_kw"]
        result.append({
            "id": z.id,
            "zone_index": z.zone_index,

            "A": {"lat": z.A.lat, "lon": z.A.lon},
            "B": {"lat": z.B.lat, "lon": z.B.lon},
            "C": {"lat": z.C.lat, "lon": z.C.lon},
            "D": {"lat": z.D.lat, "lon": z.D.lon},

            "power_kw": power_kw,
            "avg_wind_speed": z.avg_wind_speed,
            "air_density": z.air_density,
        })

    return JsonResponse(result, safe=False)

from django.http import JsonResponse
from analysis.models import Region
from analysis.services.water_gee import get_water_polygons

def get_water(request, region_id):
    try:
        region = Region.objects.select_related("A", "B", "C", "D").get(id=region_id)
    except Region.DoesNotExist:
        return JsonResponse({"error": "Region not found"}, status=404)

    # Create bounding coords
    lats = [region.A.lat, region.B.lat, region.C.lat, region.D.lat]
    lons = [region.A.lon, region.B.lon, region.C.lon, region.D.lon]

    try:
        water_fc = get_water_polygons(
            min(lats), min(lons), max(lats), max(lons)
        )
    except Exception as e:
        # Always return VALID JSON so React doesn't die
        return JsonResponse({
            "type": "FeatureCollection",
            "features": [],
            "error": str(e)
        })

    return JsonResponse(water_fc)

from .services.grid_osm import get_grid_infrastructure
from .models import Region
from django.http import JsonResponse

def get_region_grid(request, region_id):
    try:
        r = Region.objects.get(pk=region_id)
    except Region.DoesNotExist:
        return JsonResponse({"error": "Region not found"}, status=404)

    # Compute region bounding box
    lat_min = min(r.A.lat, r.B.lat, r.C.lat, r.D.lat)
    lat_max = max(r.A.lat, r.B.lat, r.C.lat, r.D.lat)
    lon_min = min(r.A.lon, r.B.lon, r.C.lon, r.D.lon)
    lon_max = max(r.A.lon, r.B.lon, r.C.lon, r.D.lon)

    grid = get_grid_infrastructure(lat_min, lon_min, lat_max, lon_max)

    return JsonResponse(grid, safe=False)


