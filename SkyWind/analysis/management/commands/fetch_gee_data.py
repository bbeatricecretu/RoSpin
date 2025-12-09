"""
fetch_gee_data.py
-----------------

This command fetches all Earth Engine data for each RegionGrid:

    1. Temperature
    2. Wind speed + direction
    3. DEM (min/max elevation + roughness)
    4. Air density
    5. Wind power density
    6. Land cover classification
    7. Potential scoring
    8. Region-level metrics (wind rose, rating)

Relies on:
    analysis.core.gee_data
    analysis.core.wind
    analysis.models
"""

from django.core.management.base import BaseCommand
from analysis.models import RegionGrid, Zone
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


class Command(BaseCommand):
    help = "Fetch all GEE data for each RegionGrid and update zone + region metrics."

    def handle(self, *args, **options):

        grids = RegionGrid.objects.all()
        if not grids.exists():
            self.stdout.write(self.style.ERROR("❌ No RegionGrid objects found."))
            return

        for grid in grids:
            region = grid.region

            self.stdout.write(self.style.NOTICE(
                f"\n🌍 Processing RegionGrid {grid.id} (Region {region.id}, "
                f"{grid.zones_per_edge}×{grid.zones_per_edge})"
            ))

            zones = list(grid.zones.all())
            if not zones:
                self.stdout.write(self.style.WARNING("⚠ No zones in this grid. Skipping."))
                continue

            # -------------------------------------------------------------
            # STEP 1 — Temperature at region center
            # -------------------------------------------------------------
            try:
                temp = get_avg_temperature(region.center.lat, region.center.lon)
                region.avg_temperature = temp
                region.save()
                self.stdout.write(self.style.SUCCESS(f"🌡 Temperature OK = {temp:.2f}°C"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Temperature error: {e}"))
                continue

            # -------------------------------------------------------------
            # STEP 2 — Wind speed & direction for each zone
            # -------------------------------------------------------------
            centers = []
            for z in zones:
                lat = round((z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4, 5)
                lon = round((z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4, 5)
                centers.append((lat, lon))

            try:
                wind_data = get_avg_wind_speeds(centers)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Wind speed error: {e}"))
                continue

            missing = 0
            for z, (lat, lon) in zip(zones, centers):
                data = wind_data.get((lat, lon))
                if not data:
                    missing += 1
                    z.avg_wind_speed = 0.0
                    z.wind_direction = 0.0
                else:
                    z.avg_wind_speed = round(data["speed"], 2)
                    z.wind_direction = round(data["direction"], 1)
                z.save()

            self.stdout.write(self.style.SUCCESS(
                f"💨 Wind updated"
            ))

            # -------------------------------------------------------------
            # BUILD SHARED ZONE DATA STRUCTURES
            # (Used by DEM, air density, power density, and land cover)
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
            # STEP 3 — DEM (min/max altitude + roughness)
            # -------------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🗺 DEM..."))

                dem_img = get_dem_layers()

                reducer = (
                    ee.Reducer.mean()
                    .combine(ee.Reducer.minMax(), sharedInputs=True)
                    .combine(ee.Reducer.stdDev(), sharedInputs=True)
                )

                result = dem_img.reduceRegions(
                    collection=fc,
                    reducer=reducer,
                    scale=30
                ).getInfo()

                for f in result["features"]:
                    props = f["properties"]
                    z = zone_map.get(int(props["zone_id"]))
                    if not z:
                        continue

                    z.min_alt = round(float(props.get("elevation_min", 0.0)), 2)
                    z.max_alt = round(float(props.get("elevation_max", 0.0)), 2)
                    z.roughness = round(float(props.get("tri_stdDev", 0.0)), 2)

                    z.save()

                self.stdout.write(self.style.SUCCESS("✅ DEM updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ DEM error: {e}"))

            # -------------------------------------------------------------
            # STEP 4 — Air density
            # -------------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🌫 Air density..."))

                img = get_air_density_image()
                res = img.reduceRegions(
                    collection=fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for f in res["features"]:
                    z = zone_map.get(int(f["properties"]["zone_id"]))
                    if not z:
                        continue
                    z.air_density = round(float(f["properties"].get("mean", 0.0)), 3)
                    z.save()

                self.stdout.write(self.style.SUCCESS("💨 Air density updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Air density error: {e}"))

            # -------------------------------------------------------------
            # STEP 5 — Wind power density
            # -------------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("⚡ Power density..."))

                img = get_wind_power_density_image()
                res = img.reduceRegions(
                    collection=fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for f in res["features"]:
                    z = zone_map.get(int(f["properties"]["zone_id"]))
                    if not z:
                        continue
                    z.power_avg = round(float(f["properties"].get("mean", 0.0)), 1)
                    z.save()

                self.stdout.write(self.style.SUCCESS("⚡ Power density updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Power density error: {e}"))

            # -------------------------------------------------------------
            # STEP 6 — Land cover
            # -------------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🏞 Land cover..."))

                img = get_landcover_image()

                # We use frequency histogram instead of mode
                lc_res = img.reduceRegions(
                    collection=fc,
                    reducer=ee.Reducer.frequencyHistogram(),
                    scale=10
                ).getInfo()

                for feat in lc_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    z = zone_map.get(int(zid))
                    if not z:
                        continue

                    hist = props.get("histogram")

                    # If no histogram → empty dict
                    if not hist:
                        z.land_type = {}
                        z.save()
                        continue

                    # FIX: Convert histogram to int keys and float values
                    # GEE returns string keys like "40", "50"
                    hist_clean = {}
                    for k, v in hist.items():
                        try:
                            class_id = int(float(k))  # Handle "40.0" or "40"
                            count = float(v)
                            hist_clean[class_id] = count
                        except (ValueError, TypeError):
                            continue

                    if not hist_clean:
                        z.land_type = {}
                        z.save()
                        continue

                    # Calculate total pixels for percentage calculation
                    total_pixels = sum(hist_clean.values())
                    
                    # Build dict with percentages for ALL classes
                    land_type_percentages = {}
                    for class_id, count in hist_clean.items():
                        label = WORLD_COVER_CLASSES.get(class_id, f"class_{class_id}")
                        percentage = round((count / total_pixels) * 100, 1)
                        land_type_percentages[label] = percentage
                    
                    # Sort by percentage descending and save
                    z.land_type = dict(sorted(land_type_percentages.items(), key=lambda x: x[1], reverse=True))
                    z.save()

                self.stdout.write(self.style.SUCCESS("🏞 Land cover updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Land cover error: {e}"))

            # -------------------------------------------------------------
            # STEP 7 — Potential scoring with gradual land suitability
            # -------------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("📈 Potential..."))

                # Land suitability scores for each land cover class
                LAND_SUITABILITY_SCORES = {
                    "Grassland": 1.0,
                    "Bare / sparse": 1.0,
                    "Cropland": 0.9,
                    "Shrubland": 1.0,
                    "Tree cover": 0.4,
                    "Moss / lichen": 0.4,
                    "Built-up": 0.0,
                    "Permanent water": 0.0,
                    "Herbaceous wetland": 0.0,
                    "Snow / ice": 0.0,
                    "Mangroves": 0.0,
                }

                HARD_EXCLUSION = {
                    "Built-up",
                    "Permanent water",
                    "Herbaceous wetland",
                    "Snow / ice",
                    "Mangroves",
                }

                def compute_land_suitability(land_type_dict):
                    """Calculate land suitability with gradual buildable fraction penalty."""
                    if not land_type_dict:
                        return 0.0, 0.0
                    
                    buildable_fraction = 0.0
                    weighted_suitability = 0.0
                    
                    for land_class, percentage in land_type_dict.items():
                        fraction = percentage / 100.0
                        suitability = LAND_SUITABILITY_SCORES.get(land_class, 0.5)
                        
                        if land_class not in HARD_EXCLUSION:
                            buildable_fraction += fraction
                            weighted_suitability += fraction * suitability
                    
                    # No hard threshold - gradual penalty
                    if buildable_fraction > 0:
                        S_land = weighted_suitability / buildable_fraction
                    else:
                        S_land = 0.0
                    
                    # Effective land score includes buildable fraction penalty
                    S_land_effective = S_land * buildable_fraction
                    
                    return S_land_effective, buildable_fraction

                def score(z):
                    # Wind component
                    S_wind = min(1.25, (z.power_avg or 0.0) / 800)
                    
                    # Terrain component
                    S_terrain = 1 - min(1.0, (z.roughness or 0.0) / 50)
                    
                    # Land suitability component (gradual)
                    land_types = z.land_type if isinstance(z.land_type, dict) else {}
                    S_land_effective, _ = compute_land_suitability(land_types)
                    
                    # Combined calculation
                    S_base = 0.7 * S_wind + 0.3 * S_terrain
                    
                    return round(100 * S_base * S_land_effective, 1)

                for z in zones:
                    z.potential = score(z)
                    z.save()

                self.stdout.write(self.style.SUCCESS("📊 Potential updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Potential error: {e}"))

            # -------------------------------------------------------------
            # STEP 8 — Compute region wind rose + metrics
            # -------------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("📘 Region metrics..."))

                # Wind rose
                region.wind_rose = compute_wind_rose(zones)

                # Basic numbers
                region.avg_potential = sum(z.potential for z in zones) / len(zones)
                region.max_potential = max(zones, key=lambda z: z.potential)
                region.infrastructure_rating = (
                    sum(z.infrastructure.index for z in zones) / len(zones)
                )
                region.index_average = sum(z.zone_index for z in zones) / len(zones)
                region.rating = int(region.avg_potential * 10)

                region.save()
                self.stdout.write(self.style.SUCCESS("🏁 Region metrics updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Region metrics error: {e}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 All RegionGrids processed successfully!"))
