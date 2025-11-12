from django.core.management.base import BaseCommand
from analysis.models import Region
from analysis.core.gee_data import get_avg_temperature, get_avg_wind_speeds


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

        self.stdout.write(self.style.SUCCESS("\n✅ All regions processed successfully."))
