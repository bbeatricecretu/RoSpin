from django.core.management.base import BaseCommand
from analysis.models import Region, Zone, Point, Infrastructure
from analysis.core.entities import Region as RegionEntity, Point as PointEntity


class Command(BaseCommand):
    help = "Generate zones for all regions using geometric logic and save them to the database"

    def handle(self, *args, **options):
        # Ensure at least one infrastructure reference exists
        infra, _ = Infrastructure.objects.get_or_create(index=1)

        for region_db in Region.objects.all():
            self.stdout.write(f"Generating zones for region centered at ({region_db.center.lat}, {region_db.center.lon})")

            # 1️⃣ Convert Django Region to your Python RegionEntity
            region_entity = RegionEntity(center=PointEntity(region_db.center.lat, region_db.center.lon))
            region_entity.generate_corners(side_km=20.0)
            region_entity.generate_grid(n=5)

            A, _ = Point.objects.get_or_create(lat=region_entity.A.lat, lon=region_entity.A.lon)
            B, _ = Point.objects.get_or_create(lat=region_entity.B.lat, lon=region_entity.B.lon)
            C, _ = Point.objects.get_or_create(lat=region_entity.C.lat, lon=region_entity.C.lon)
            D, _ = Point.objects.get_or_create(lat=region_entity.D.lat, lon=region_entity.D.lon)

            region_db.A = A
            region_db.B = B
            region_db.C = C
            region_db.D = D
            region_db.save()

            # 2️⃣ Iterate through generated zones and save them as ORM objects
            count = 0
            index = 1
            for row in region_entity.zones:
                for z in row:
                    A, _ = Point.objects.get_or_create(lat=z.A.lat, lon=z.A.lon)
                    B, _ = Point.objects.get_or_create(lat=z.B.lat, lon=z.B.lon)
                    C, _ = Point.objects.get_or_create(lat=z.C.lat, lon=z.C.lon)
                    D, _ = Point.objects.get_or_create(lat=z.D.lat, lon=z.D.lon)

                    Zone.objects.get_or_create(
                        region=region_db,
                        A=A, B=B, C=C, D=D,
                        infrastructure=infra,
                        zone_index = index
                    )
                    count += 1
                    index += 1
            region_db.compute_from_zones()
            self.stdout.write(self.style.SUCCESS(f"✅ Generated and   saved {count} zones for region {region_db.id}"))
