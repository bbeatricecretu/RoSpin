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

            # --- Step 1: Temperature for region center ---
            try:
                temp = get_avg_temperature(region.center.lat, region.center.lon)
                region.avg_temperature = temp
                region.save()
                self.stdout.write(self.style.SUCCESS(f"🌡️  Avg temperature: {temp} °C"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to fetch temperature: {e}"))
                continue

            # --- Step 2: Wind speeds for zones (batched) ---
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

            # ==========================================================
            # STEP 3: DEM (elevation, slope, TRI) extraction (fixed)
            # ==========================================================
            try:
                self.stdout.write(self.style.NOTICE("🗺  Extracting DEM metrics (elevation, slope, tri)..."))

                dem_image = get_dem_layers()

                features = []
                for z in zones:
                    # Create polygon geometry for the zone
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

                # Add stdDev to reducer for TRI-like roughness
                reducer = (
                    ee.Reducer.mean()
                    .combine(reducer2=ee.Reducer.minMax(), sharedInputs=True)
                    .combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)
                )

                # Reduce over each zone polygon
                results = dem_image.reduceRegions(
                    collection=zones_fc,
                    reducer=reducer,
                    scale=30
                ).getInfo()

                for feat in results["features"]:
                    props = feat["properties"]
                    zone_id = props.get("zone_id")

                    try:
                        zone = Zone.objects.get(id=zone_id)
                    except Zone.DoesNotExist:
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


        self.stdout.write(self.style.SUCCESS("\n✅ All regions processed successfully."))
