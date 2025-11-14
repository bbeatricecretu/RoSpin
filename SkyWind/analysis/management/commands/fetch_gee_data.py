from django.core.management.base import BaseCommand
from analysis.models import *
from analysis.core.gee_data import *


class Command(BaseCommand):
    help = "Fetches GEE temperature and wind data for all regions and zones (optimized batch version)."

    def handle(self, *args, **options):
        regions = Region.objects.all()
        if not regions.exists():
            self.stdout.write(self.style.WARNING("No regions found in database."))
            return

        for region in regions:
            self.stdout.write(
                self.style.NOTICE(f"\n🌍 Processing region centered at ({region.center.lat}, {region.center.lon})...")
            )

            # ---------- Step 1: Temperature for region center ---------- 
            try:
                temp = get_avg_temperature(region.center.lat, region.center.lon)
                region.avg_temperature = temp
                region.save()
                self.stdout.write(self.style.SUCCESS(f"🌡️  Avg temperature: {temp} °C"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to fetch temperature: {e}"))
                continue

            # ---------- Step 2: Wind speeds for zones (batched) ---------- 
            zones = list(region.zones.all())
            if not zones:
                self.stdout.write(self.style.WARNING("No zones found for this region. Skipping wind computation."))
                continue

            # Compute approximate center (lat, lon) for each zone
            points = [
                (
                    (z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4,
                    (z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4
                )
                for z in zones
            ]

            try:
                wind_dict = get_avg_wind_speeds(points)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error fetching wind data: {e}"))
                continue

            # Update each zone with fetched value
            for zone, (lat, lon) in zip(zones, points):
                ws = wind_dict.get((lat, lon))
                if ws is not None:
                    zone.avg_wind_speed = ws
                    zone.save()

            self.stdout.write(
                self.style.SUCCESS(f"💨 Updated wind data for {len(zones)} zones.")
            )
            # ---------- STEP 3: DEM (elevation, slope, TRI) extraction ----------
            try:
                self.stdout.write(self.style.NOTICE("🗺  Extracting DEM metrics (elevation, slope, tri)..."))

                dem_image = get_dem_layers()

                # map zone.id -> zone object for quick lookup
                zone_by_id = {z.id: z for z in zones}

                features = []
                for z in zones:
                    coords = [
                        [z.A.lon, z.A.lat],
                        [z.B.lon, z.B.lat],
                        [z.C.lon, z.C.lat],
                        [z.D.lon, z.D.lat],
                        [z.A.lon, z.A.lat],  # close polygon
                    ]
                    geom = ee.Geometry.Polygon([coords])
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
                    zid = props.get("zone_id")
                    if zid is None:
                        continue

                    zone = zone_by_id.get(int(zid))
                    if zone is None:
                        continue

                    elev_min = props.get("elevation_min")
                    elev_max = props.get("elevation_max")
                    tri_std = props.get("tri_stdDev") or props.get("tri_mean")

                    if elev_min is not None:
                        zone.min_alt = round(float(elev_min), 2)
                    if elev_max is not None:
                        zone.max_alt = round(float(elev_max), 2)
                    if tri_std is not None:
                        zone.roughness = round(float(tri_std), 2)

                    zone.save()

                self.stdout.write(self.style.SUCCESS("✅ DEM metrics updated successfully."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed DEM extraction: {e}"))


            # ---------- STEP 4: Air density (kg/m³) ----------
            try:
                self.stdout.write(self.style.NOTICE("🌫  Computing air density..."))
                air_img = get_air_density_image(year=2023)
                air_res = air_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for feat in air_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    val = props.get("mean")  # Earth Engine used 'mean' as key

                    if zid is None or val is None:
                        continue

                    zone = zone_by_id.get(int(zid))
                    if zone is None:
                        continue

                    zone.air_density = round(float(val), 3)
                    zone.save()

                self.stdout.write(self.style.SUCCESS("✅ Air density updated."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Air density failed: {e}"))


            # ---------- STEP 5: Wind power density (W/m²) ----------
            try:
                self.stdout.write(self.style.NOTICE("⚡ Computing mean wind power density..."))
                wpd_img = get_wind_power_density_image(year=2023)
                wpd_res = wpd_img.reduceRegions(
                    collection=zones_fc,
                    reducer=ee.Reducer.mean(),
                    scale=1000
                ).getInfo()

                for feat in wpd_res["features"]:
                    props = feat["properties"]
                    zid = props.get("zone_id")
                    val = props.get("mean")  # again, 'mean' is the key

                    if zid is None or val is None:
                        continue

                    zone = zone_by_id.get(int(zid))
                    if zone is None:
                        continue

                    zone.power_avg = round(float(val), 1)
                    zone.save()

                self.stdout.write(self.style.SUCCESS("✅ Power density updated."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Power density failed: {e}"))


            # ---------- STEP 6: Dominant land type (mode) ----------
            try:
                self.stdout.write(self.style.NOTICE("🗺  Classifying dominant land type..."))
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

                    if zid is None or clz is None:
                        continue

                    zone = zone_by_id.get(int(zid))
                    if zone is None:
                        continue

                    label = WORLD_COVER_CLASSES.get(int(round(clz)))
                    if label:
                        zone.land_type = label
                        zone.save()

                self.stdout.write(self.style.SUCCESS("✅ Land type updated."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Land type failed: {e}"))


            # ---------- STEP 7: Potential (simple, explainable score) ----------
            try:
                self.stdout.write(self.style.NOTICE("📈 Computing zone potential..."))
                EXCLUDED = {"Built-up", "Permanent water", "Herbaceous wetland", "Snow / ice", "Mangroves"}

                def score_zone(z: Zone) -> float:
                    wpd = max(0.0, min(1000.0, z.power_avg))
                    wpd_score = wpd / 800.0
                    rough = max(0.0, min(50.0, float(z.roughness)))
                    rough_score = 1.0 - (rough / 50.0)
                    land_penalty = 0.0 if z.land_type in EXCLUDED else 1.0
                    base = 0.7 * wpd_score + 0.3 * rough_score
                    return round(100.0 * base * land_penalty, 1)

                for z in zones:
                    z.potential = score_zone(z)
                    z.save()

                self.stdout.write(self.style.SUCCESS("✅ Potential score updated."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Potential scoring failed: {e}"))



        self.stdout.write(self.style.SUCCESS("\n✅ All regions processed successfully."))
