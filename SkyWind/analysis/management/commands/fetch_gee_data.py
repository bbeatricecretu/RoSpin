from django.core.management.base import BaseCommand
from analysis.models import Region, RegionGrid, Zone
from analysis.core.gee_data import (
    get_avg_temperature,
    get_avg_wind_speeds,
    get_dem_layers,
    get_air_density_image,
    get_wind_power_density_image,
    get_landcover_image,
    WORLD_COVER_CLASSES
)
import ee


class Command(BaseCommand):
    help = "Fetch GEE temperature, wind (speed+direction), DEM, air density, land type and compute potential."

    def handle(self, *args, **options):

        grids = RegionGrid.objects.all()
        if not grids.exists():
            self.stdout.write(self.style.WARNING("No RegionGrids found."))
            return

        for grid in grids:
            region = grid.region

            self.stdout.write(self.style.NOTICE(
                f"\n🌍 Processing RegionGrid {grid.id} for Region {region.id} ({grid.zones_per_edge}×{grid.zones_per_edge})"
            ))

            # ---------------------------------------------------------
            # STEP 1 — Region center temperature
            # ---------------------------------------------------------
            try:
                temp = get_avg_temperature(region.center.lat, region.center.lon)
                region.avg_temperature = temp
                region.save()
                self.stdout.write(self.style.SUCCESS(f"🌡 Temperature = {temp:.2f} °C"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Temperature failed: {e}"))
                continue

            # ---------------------------------------------------------
            # STEP 2 — Wind speeds + direction for zones
            # ---------------------------------------------------------
            zones = list(grid.zones.all())

            if not zones:
                self.stdout.write(self.style.WARNING("⚠ No zones in grid — Skipping"))
                continue

            centers = [
                (
                    (z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4,
                    (z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4
                )
                for z in zones
            ]

            try:
                wind_dict = get_avg_wind_speeds(centers)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Wind data error: {e}"))
                continue

            # ALWAYS assign valid defaults so DB never gets NULL
            for zone, (lat, lon) in zip(zones, centers):
                data = wind_dict.get((lat, lon))

                if data and data.get("speed") is not None:
                    zone.avg_wind_speed = data.get("speed", 0.0) or 0.0
                    zone.wind_direction = data.get("direction", 0.0) or 0.0
                else:
                    # SAFE DEFAULTS
                    zone.avg_wind_speed = 0.0
                    zone.wind_direction = 0.0

                zone.save()

            self.stdout.write(self.style.SUCCESS(f"💨 Updated wind speed & direction for {len(zones)} zones."))

            # ---------------------------------------------------------
            # STEP 3 — DEM extraction
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🗺 Fetching DEM..."))

                dem_image = get_dem_layers()
                zone_by_id = {z.id: z for z in zones}

                features = []
                for z in zones:
                    poly = [
                        [z.A.lon, z.A.lat],
                        [z.B.lon, z.B.lat],
                        [z.C.lon, z.C.lat],
                        [z.D.lon, z.D.lat],
                        [z.A.lon, z.A.lat],
                    ]
                    geom = ee.Geometry.Polygon([poly])
                    features.append(ee.Feature(geom, {"zone_id": z.id}))

                zones_fc = ee.FeatureCollection(features)

                reducer = (
                    ee.Reducer.mean()
                    .combine(ee.Reducer.minMax(), sharedInputs=True)
                    .combine(ee.Reducer.stdDev(), sharedInputs=True)
                )

                results = dem_image.reduceRegions(
                    collection=zones_fc,
                    reducer=reducer,
                    scale=30
                ).getInfo()

                for feat in results["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    z = zone_by_id.get(int(zid))

                    if not z:
                        continue

                    z.min_alt = round(float(props.get("elevation_min") or 0.0), 2)
                    z.max_alt = round(float(props.get("elevation_max") or 0.0), 2)
                    tri_std = props.get("tri_stdDev") or props.get("tri_mean") or 0.0
                    z.roughness = round(float(tri_std), 2)

                    z.save()

                self.stdout.write(self.style.SUCCESS("✅ DEM updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ DEM failed: {e}"))

            # ---------------------------------------------------------
            # STEP 4 — Air density
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🌫 Air density..."))

                air_img = get_air_density_image(2023)
                air_res = air_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for feat in air_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    z = zone_by_id.get(int(zid))
                    val = props.get("mean")

                    if not z:
                        continue

                    z.air_density = round(float(val or 0.0), 3)
                    z.save()

                self.stdout.write(self.style.SUCCESS("💨 Air density updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Air density failed: {e}"))

            # ---------------------------------------------------------
            # STEP 5 — Wind power density
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("⚡ Wind power density..."))

                wpd_img = get_wind_power_density_image(2023)
                wpd_res = wpd_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for feat in wpd_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    z = zone_by_id.get(int(zid))
                    val = props.get("mean")

                    if not z:
                        continue

                    z.power_avg = round(float(val or 0.0), 1)
                    z.save()

                self.stdout.write(self.style.SUCCESS("⚡ Wind power density updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Power density failed: {e}"))

            # ---------------------------------------------------------
            # STEP 6 — Land cover
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🗺 Land cover..."))

                lc_img = get_landcover_image(2021)
                lc_res = lc_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mode(),
                    scale=10
                ).getInfo()

                for feat in lc_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    z = zone_by_id.get(int(zid))
                    clz = props.get("mode")

                    if not z:
                        continue

                    if clz is not None:
                        label = WORLD_COVER_CLASSES.get(int(round(clz)))
                        z.land_type = label or ""
                    else:
                        z.land_type = ""

                    z.save()

                self.stdout.write(self.style.SUCCESS("🏞 Land cover updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Land cover failed: {e}"))

            # ---------------------------------------------------------
            # STEP 7 — Potential
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("📈 Scoring potential..."))

                EXCLUDED = {"Built-up", "Permanent water", "Herbaceous wetland", "Snow / ice", "Mangroves"}

                def score_zone(z):
                    wpd_score = min(1.25, (z.power_avg or 0.0) / 800)
                    rough_score = 1 - min(1.0, (z.roughness or 0.0) / 50)
                    land_penalty = 0 if z.land_type in EXCLUDED else 1
                    return round(100 * (0.7 * wpd_score + 0.3 * rough_score) * land_penalty, 1)

                for z in zones:
                    z.potential = score_zone(z)
                    z.save()

                self.stdout.write(self.style.SUCCESS("📊 Potential updated."))

                # -----------------------------------------------------
                # FINAL — Region metrics + wind rose
                # -----------------------------------------------------
                try:
                    self.stdout.write(self.style.NOTICE("📘 Updating region metrics..."))
                    region.compute_from_zones(grid)
                    self.stdout.write(self.style.SUCCESS("🏁 Region metrics updated."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Region metric update failed: {e}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Potential failed: {e}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 All RegionGrids processed successfully."))
