import ee
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


EXCLUDED_LAND = {
    "Built-up",
    "Permanent water",
    "Herbaceous wetland",
    "Snow / ice",
    "Mangroves",
}


def compute_gee_for_grid(grid: RegionGrid):
    """
    FULL 1:1 REPLICATION of fetch_gee_data logic.
    This ensures frontend API returns *identical* values.
    """

    region = grid.region
    zones = list(grid.zones.all())

    if not zones:
        return

    # -------------------------------------------------------------
    # STEP 1 — Temperature at region center
    # -------------------------------------------------------------
    temp = get_avg_temperature(region.center.lat, region.center.lon)
    region.avg_temperature = temp
    region.save()

    # -------------------------------------------------------------
    # STEP 2 — Wind per zone
    # -------------------------------------------------------------
    centers = []
    for z in zones:
        lat = round((z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4, 5)
        lon = round((z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4, 5)
        centers.append((lat, lon))

    wind_data = get_avg_wind_speeds(centers)

    for z, (lat, lon) in zip(zones, centers):
        data = wind_data.get((lat, lon))
        if not data:
            z.avg_wind_speed = 0.0
            z.wind_direction = 0.0
        else:
            z.avg_wind_speed = round(data["speed"], 2)
            z.wind_direction = round(data["direction"], 1)
        z.save()

    # -------------------------------------------------------------
    # Build FeatureCollection for DEM, LC, Air, Power
    # -------------------------------------------------------------
    zone_map = {z.id: z for z in zones}

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

    # -------------------------------------------------------------
    # STEP 3 — DEM
    # -------------------------------------------------------------
    dem_img = get_dem_layers()
    reducer = (
        ee.Reducer.mean()
        .combine(ee.Reducer.minMax(), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True)
    )

    dem = dem_img.reduceRegions(fc, reducer, scale=30).getInfo()

    for f in dem["features"]:
        props = f["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        z.min_alt = round(float(props.get("elevation_min", 0.0)), 2)
        z.max_alt = round(float(props.get("elevation_max", 0.0)), 2)
        z.roughness = round(float(props.get("tri_stdDev", 0.0)), 2)
        z.save()

    # -------------------------------------------------------------
    # STEP 4 — Air density
    # -------------------------------------------------------------
    img = get_air_density_image()
    air = img.reduceRegions(fc, ee.Reducer.mean(), scale=1000).getInfo()

    for f in air["features"]:
        props = f["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        z.air_density = round(float(props.get("mean", 0.0)), 3)
        z.save()

    # -------------------------------------------------------------
    # STEP 5 — Power density
    # -------------------------------------------------------------
    img = get_wind_power_density_image()
    pw = img.reduceRegions(fc, ee.Reducer.mean(), scale=1000).getInfo()

    for f in pw["features"]:
        props = f["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        z.power_avg = round(float(props.get("mean", 0.0)), 1)
        z.save()

    # -------------------------------------------------------------
    # STEP 6 — Land cover
    # -------------------------------------------------------------
    img = get_landcover_image()
    lc = img.reduceRegions(fc, ee.Reducer.frequencyHistogram(), scale=10).getInfo()

    for feat in lc["features"]:
        props = feat["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        hist = props.get("histogram")
        if not hist:
            z.land_type = ""
            z.save()
            continue

        max_count = max(hist.values())
        dom_classes = [int(k) for k, v in hist.items() if v == max_count]
        labels = [WORLD_COVER_CLASSES.get(c, f"class_{c}") for c in dom_classes]

        z.land_type = ", ".join(labels)
        z.save()

    # -------------------------------------------------------------
    # STEP 7 — Potential (identical formula)
    # -------------------------------------------------------------
    for z in zones:
        wpd = (z.power_avg or 0.0) / 800
        wpd = min(1.25, wpd)
        rough = 1 - min(1.0, (z.roughness or 0.0) / 50)
        ok_land = 0 if z.land_type in EXCLUDED_LAND else 1

        z.potential = round(100 * (0.7 * wpd + 0.3 * rough) * ok_land, 1)
        z.save()

    # -------------------------------------------------------------
    # STEP 8 — Region metrics (identical)
    # -------------------------------------------------------------
    region.wind_rose = compute_wind_rose(zones)
    region.avg_potential = sum(z.potential for z in zones) / len(zones)
    region.rating = int(region.avg_potential * 10)
    region.save()
