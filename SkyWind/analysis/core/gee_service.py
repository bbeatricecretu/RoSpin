# analysis/core/gee_service.py

from analysis.models import Zone, RegionGrid
from analysis.core.gee_data import (
    get_avg_temperature,
    get_avg_wind_speeds,
    get_dem_layers,
    get_air_density_image,
    get_wind_power_density_image,
    get_landcover_image,
    WORLD_COVER_CLASSES,
)
from analysis.core.wind import compute_wind_rose
import ee

def compute_gee_for_grid(grid: RegionGrid):
    """Compute all GEE data for this ONE grid only."""


    print("TEMP GEE SERVICE: compute_gee_for_grid was called.")
    region = grid.region
    zones = list(grid.zones.all())

    # ---------------------
    # 1) Temperature
    # ---------------------
    region.avg_temperature = get_avg_temperature(
        region.center.lat, region.center.lon
    )
    region.save()

    # ---------------------
    # 2) Wind for each zone
    # ---------------------
    centers = []
    for z in zones:
        lat = round((z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4, 5)
        lon = round((z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4, 5)
        centers.append((lat, lon))

    wind_data = get_avg_wind_speeds(centers)

    for z, (lat, lon) in zip(zones, centers):
        d = wind_data.get((lat, lon))
        if d:
            z.avg_wind_speed = d["speed"]
            z.wind_direction = d["direction"]
        z.save()

    # ---------------------
    # Build FC for DEM / LC
    # ---------------------
    features = []
    for z in zones:
        poly = [
            [z.A.lon, z.A.lat],
            [z.B.lon, z.B.lat],
            [z.C.lon, z.C.lat],
            [z.D.lon, z.D.lat],
            [z.A.lon, z.A.lat],
        ]
        features.append(ee.Feature(
            ee.Geometry.Polygon([poly]),
            {"zone_id": z.id}
        ))

    fc = ee.FeatureCollection(features)

    # ---------------------
    # 3) DEM
    # ---------------------
    dem = get_dem_layers()
    reducer = (
        ee.Reducer.mean()
        .combine(ee.Reducer.minMax(), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True)
    )

    dem_res = dem.reduceRegions(collection=fc, reducer=reducer, scale=30).getInfo()

    for f in dem_res["features"]:
        zid = int(f["properties"]["zone_id"])
        z = next((x for x in zones if x.id == zid), None)
        p = f["properties"]
        if z:
            z.min_alt = p.get("elevation_min", 0)
            z.max_alt = p.get("elevation_max", 0)
            z.roughness = p.get("tri_stdDev", 0)
            z.save()

    # ---------------------
    # 4) Air density
    # ---------------------
    air_img = get_air_density_image()
    air_res = air_img.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=1000
    ).getInfo()

    for f in air_res["features"]:
        zid = int(f["properties"]["zone_id"])
        z = next((x for x in zones if x.id == zid), None)
        if z:
            z.air_density = f["properties"].get("mean", 0)
            z.save()

    # ---------------------
    # 5) Power density
    # ---------------------
    pw_img = get_wind_power_density_image()
    pw_res = pw_img.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=1000
    ).getInfo()

    for f in pw_res["features"]:
        zid = int(f["properties"]["zone_id"])
        z = next((x for x in zones if x.id == zid), None)
        if z:
            z.power_avg = f["properties"].get("mean", 0)
            z.save()

    # ---------------------
    # 6) Land cover
    # ---------------------
    lc_img = get_landcover_image()
    lc_res = lc_img.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.frequencyHistogram(),
        scale=10
    ).getInfo()

    for f in lc_res["features"]:
        zid = int(f["properties"]["zone_id"])
        z = next((x for x in zones if z.id == zid), None)
        hist = f["properties"].get("histogram")
        if not z or not hist:
            continue

        max_count = max(hist.values())
        dominant = [WORLD_COVER_CLASSES.get(int(k)) for k, v in hist.items() if v == max_count]
        z.land_type = ", ".join(dominant)
        z.save()

    # ---------------------
    # 7) Potential
    # ---------------------
    for z in zones:
        wpd = min(1.25, (z.power_avg or 0) / 800)
        rough = 1 - min(1, (z.roughness or 0) / 50)
        good_land = 1 if "Built-up" not in z.land_type else 0
        z.potential = 100 * (0.7 * wpd + 0.3 * rough) * good_land
        z.save()

    # ---------------------
    # 8) Region metrics
    # ---------------------
    region.wind_rose = compute_wind_rose(zones)
    region.avg_potential = sum(z.potential for z in zones) / len(zones)
    region.rating = int(region.avg_potential * 10)
    region.save()
