from django.core.management.base import BaseCommand
from analysis.models import Region, RegionGrid, Zone
from analysis.core.gee_data import *
import ee


class Command(BaseCommand):
    help = "Fetch GEE temperature, wind, DEM, air density, land type, and compute potential for all RegionGrids."

    def handle(self, *args, **options):

        grids = RegionGrid.objects.all()
        if not grids.exists():
            self.stdout.write(self.style.WARNING("No RegionGrid objects found."))
            return

        for grid in grids:
            region = grid.region
            self.stdout.write(self.style.NOTICE(
                f"\n🌍 Processing RegionGrid {grid.id} (Region {region.id}, {grid.zones_per_edge}x{grid.zones_per_edge})"
            ))

            # ---------------------------------------------------------
            # STEP 1 — Region center temperature
            # ---------------------------------------------------------
            try:
                temp = get_avg_temperature(region.center.lat, region.center.lon)
                region.avg_temperature = temp
                region.save()
                self.stdout.write(self.style.SUCCESS(f"🌡 Avg temperature: {temp:.2f} °C"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Temperature fetch failed: {e}"))
                continue

            # ---------------------------------------------------------
            # STEP 2 — Wind speeds for zones
            # ---------------------------------------------------------
            zones = list(grid.zones.all())

            if not zones:
                self.stdout.write(self.style.WARNING("⚠ No zones found for this RegionGrid. Skipping wind."))
                continue

            centers = [
                (
                    (z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4,
                    (z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4
                ) for z in zones
            ]

            try:
                wind_dict = get_avg_wind_speeds(centers)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Wind speed fetch error: {e}"))
                continue

            for zone, (lat, lon) in zip(zones, centers):
                ws = wind_dict.get((lat, lon))
                if ws is not None:
                    zone.avg_wind_speed = ws
                    zone.save()

            self.stdout.write(self.style.SUCCESS(f"💨 Updated wind data for {len(zones)} zones."))

            # ---------------------------------------------------------
            # STEP 3 — DEM extraction
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🗺 Extracting DEM metrics..."))

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
                    .combine(reducer2=ee.Reducer.minMax(), sharedInputs=True)
                    .combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)
                )

                results = dem_image.reduceRegions(
                    collection=zones_fc,
                    reducer=reducer,
                    scale=30
                ).getInfo()

                for feat in results["features"]:
                    props = feat["properties"]
                    z_id = props.get("zone_id")
                    z = zone_by_id.get(int(z_id))

                    if z:
                        if props.get("elevation_min") is not None:
                            z.min_alt = round(float(props["elevation_min"]), 2)
                        if props.get("elevation_max") is not None:
                            z.max_alt = round(float(props["elevation_max"]), 2)
                        tri_std = props.get("tri_stdDev") or props.get("tri_mean")
                        if tri_std is not None:
                            z.roughness = round(float(tri_std), 2)
                        z.save()

                self.stdout.write(self.style.SUCCESS("✅ DEM metrics updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ DEM extraction failed: {e}"))

            # ---------------------------------------------------------
            # STEP 4 — Air density
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🌫 Fetching air density..."))

                air_img = get_air_density_image(year=2023)
                air_res = air_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for feat in air_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    z = zone_by_id.get(int(zid))
                    if z and props.get("mean") is not None:
                        z.air_density = round(float(props["mean"]), 3)
                        z.save()

                self.stdout.write(self.style.SUCCESS("💨 Air density updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Air density failed: {e}"))

            # ---------------------------------------------------------
            # STEP 5 — Wind power density
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("⚡ Fetching wind power density..."))

                wpd_img = get_wind_power_density_image(year=2023)
                wpd_res = wpd_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for feat in wpd_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    z = zone_by_id.get(int(zid))
                    if z and props.get("mean") is not None:
                        z.power_avg = round(float(props["mean"]), 1)
                        z.save()

                self.stdout.write(self.style.SUCCESS("⚡ Wind power density updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Power density failed: {e}"))

            # ---------------------------------------------------------
            # STEP 6 — Land type
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("🗺 Determining land cover..."))

                lc_img = get_landcover_image(year=2021)
                lc_res = lc_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mode(),
                    scale=10
                ).getInfo()

                for feat in lc_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    clz = props.get("mode")
                    z = zone_by_id.get(int(zid))
                    if z and clz is not None:
                        label = WORLD_COVER_CLASSES.get(int(round(clz)))
                        if label:
                            z.land_type = label
                            z.save()

                self.stdout.write(self.style.SUCCESS("🏞 Land type updated."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Landcover failed: {e}"))

            # ---------------------------------------------------------
            # STEP 7 — Potential
            # ---------------------------------------------------------
            try:
                self.stdout.write(self.style.NOTICE("📈 Scoring potential..."))

                EXCLUDED = {"Built-up", "Permanent water", "Herbaceous wetland", "Snow / ice", "Mangroves"}

                def score_zone(z: Zone):
                    wpd = max(0, min(1000, z.power_avg))
                    wpd_score = wpd / 800
                    rough_score = 1 - max(0, min(50, z.roughness)) / 50
                    land_penalty = 0 if z.land_type in EXCLUDED else 1
                    return round(100 * (0.7 * wpd_score + 0.3 * rough_score) * land_penalty, 1)

                for z in zones:
                    z.potential = score_zone(z)
                    z.save()

                self.stdout.write(self.style.SUCCESS("📊 Potential updated."))

                # ---------- FINAL STEP: Update Region stats ----------
                try:
                    self.stdout.write(self.style.NOTICE("📘 Updating region metrics..."))
                    region.compute_from_zones(grid)
                    self.stdout.write(self.style.SUCCESS(
                        f"🏁 Region metrics updated using RegionGrid {grid.id}"
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to update region metrics: {e}"))


            except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Potential scoring failed: {e}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 All RegionGrids processed successfully."))
