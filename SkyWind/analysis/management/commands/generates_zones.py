from django.core.management.base import BaseCommand
from analysis.models import RegionGrid, Zone, Point, Infrastructure
from analysis.core.entities import Region as RegionEntity, Point as PointEntity


class Command(BaseCommand):
    help = "Generate zones for each RegionGrid based on the grid configuration stored in the database."

    def handle(self, *args, **options):

        infra, _ = Infrastructure.objects.get_or_create(index=1)

        # LOOP REGION GRIDS — NOT REGION
        for grid in RegionGrid.objects.all():
            region_db = grid.region

            self.stdout.write(f"▶ Generating zones for RegionGrid {grid.id}: "
                              f"Region {region_db.id}, side {grid.side_km} km, {grid.zones_per_edge}x{grid.zones_per_edge}")

            # If zones already exist → skip
            if grid.zones.exists():
                self.stdout.write(self.style.WARNING(
                    f"⚠ Grid {grid.id} already has zones. Skipping."
                ))
                # RECOMPUTE CORNERS – because grid does NOT store A/B/C/D
                region_db = grid.region

                region_entity = RegionEntity(
                    center=PointEntity(region_db.center.lat, region_db.center.lon)
                )

                region_entity.generate_corners(grid.side_km)

                A, _ = Point.objects.get_or_create(lat=region_entity.A.lat, lon=region_entity.A.lon)
                B, _ = Point.objects.get_or_create(lat=region_entity.B.lat, lon=region_entity.B.lon)
                C, _ = Point.objects.get_or_create(lat=region_entity.C.lat, lon=region_entity.C.lon)
                D, _ = Point.objects.get_or_create(lat=region_entity.D.lat, lon=region_entity.D.lon)

                # update region
                region_db.A = A
                region_db.B = B
                region_db.C = C
                region_db.D = D
                region_db.save()
                continue

            # Build RegionEntity using DB values
            region_entity = RegionEntity(
                center=PointEntity(region_db.center.lat, region_db.center.lon)
            )

            # USE VALUES FROM DB
            region_entity.generate_corners(grid.side_km)
            region_entity.generate_grid(grid.zones_per_edge)

            # Save corners
            A, _ = Point.objects.get_or_create(lat=region_entity.A.lat, lon=region_entity.A.lon)
            B, _ = Point.objects.get_or_create(lat=region_entity.B.lat, lon=region_entity.B.lon)
            C, _ = Point.objects.get_or_create(lat=region_entity.C.lat, lon=region_entity.C.lon)
            D, _ = Point.objects.get_or_create(lat=region_entity.D.lat, lon=region_entity.D.lon)

            grid.A = A
            grid.B = B
            grid.C = C
            grid.D = D
            grid.save()

            # Also update the parent Region corners
            region = grid.region
            region.A = A
            region.B = B
            region.C = C
            region.D = D
            region.save()

            # Generate zones
            count = 0
            index = 1

            for row in region_entity.zones:
                for z in row:
                    # Create points
                    A, _ = Point.objects.get_or_create(lat=z.A.lat, lon=z.A.lon)
                    B, _ = Point.objects.get_or_create(lat=z.B.lat, lon=z.B.lon)
                    C, _ = Point.objects.get_or_create(lat=z.C.lat, lon=z.C.lon)
                    D, _ = Point.objects.get_or_create(lat=z.D.lat, lon=z.D.lon)

                    # Reuse existing zones (cache)
                    existing = Zone.objects.filter(A=A, B=B, C=C, D=D).first()

                    if existing:
                        Zone.objects.create(
                            grid=grid,
                            A=A, B=B, C=C, D=D,
                            infrastructure=infra,
                            zone_index=index,
                            min_alt=existing.min_alt,
                            max_alt=existing.max_alt,
                            roughness=existing.roughness,
                            air_density=existing.air_density,
                            avg_wind_speed=existing.avg_wind_speed or 0.0,
                            power_avg=existing.power_avg or 0.0,
                            land_type=existing.land_type or "",
                            potential=existing.potential or 0.0,
                        )

                    else:
                        Zone.objects.create(
                            grid=grid,
                            A=A, B=B, C=C, D=D,
                            infrastructure=infra,
                            zone_index=index
                        )

                    index += 1
                    count += 1

            self.stdout.write(self.style.SUCCESS(
                f"✔ Created {count} zones for RegionGrid {grid.id}"
            ))
