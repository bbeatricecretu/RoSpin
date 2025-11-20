"""
generate_zones.py
-----------------

This management command generates all zones for each RegionGrid.

Responsibilities:
    • Compute region corners based on center + side_km
    • Generate n×n zone polygons
    • Create Point + Zone objects in DB
    • Update Region corners
    • Reuse Infrastructure records

Requires:
    analysis.core.geometry
    analysis.models
"""

from django.core.management.base import BaseCommand
from analysis.models import RegionGrid, Zone, Point, Infrastructure
from analysis.core.geometry import compute_region_corners, generate_zone_grid


class Command(BaseCommand):
    help = "Generate zones for each RegionGrid based on region center and grid settings."

    def handle(self, *args, **options):

        infra, _ = Infrastructure.objects.get_or_create(index=1)

        for grid in RegionGrid.objects.all():

            region = grid.region

            self.stdout.write(
                f"▶ Generating zones for RegionGrid {grid.id}: "
                f"Region {region.id}, side {grid.side_km} km, "
                f"{grid.zones_per_edge}×{grid.zones_per_edge}"
            )

            # If grid already has zones → skip zone creation but recompute corners
            if grid.zones.exists():
                self.stdout.write(self.style.WARNING(
                    f"⚠ Grid {grid.id} already has zones. Updating corners only."
                ))
                self.update_region_corners(region, grid)
                continue

            # -------------------------------------------------------------
            # STEP 1 — Compute region corners
            # -------------------------------------------------------------
            corners = compute_region_corners(
                center_lat=region.center.lat,
                center_lon=region.center.lon,
                side_km=grid.side_km
            )

            # Save corners as Point objects
            A = self.get_point(*corners["A"])
            B = self.get_point(*corners["B"])
            C = self.get_point(*corners["C"])
            D = self.get_point(*corners["D"])

            # Update Region
            region.A = A
            region.B = B
            region.C = C
            region.D = D
            region.save()

            # Update RegionGrid (optional, only if you want)
            grid.A = A
            grid.B = B
            grid.C = C
            grid.D = D
            grid.save()

            # -------------------------------------------------------------
            # STEP 2 — Generate zone grid (pure geometry)
            # -------------------------------------------------------------
            zone_grid = generate_zone_grid(
                A=(A.lat, A.lon),
                B=(B.lat, B.lon),
                C=(C.lat, C.lon),
                D=(D.lat, D.lon),
                n=grid.zones_per_edge
            )

            # -------------------------------------------------------------
            # STEP 3 — Create Zone records
            # -------------------------------------------------------------
            count = 0
            zone_index = 1

            for row in zone_grid:
                for cell in row:

                    A_z = self.get_point(*cell["A"])
                    B_z = self.get_point(*cell["B"])
                    C_z = self.get_point(*cell["C"])
                    D_z = self.get_point(*cell["D"])

                    Zone.objects.create(
                        grid=grid,
                        A=A_z,
                        B=B_z,
                        C=C_z,
                        D=D_z,
                        infrastructure=infra,
                        zone_index=zone_index
                    )

                    zone_index += 1
                    count += 1

            self.stdout.write(self.style.SUCCESS(
                f"✔ Created {count} zones for RegionGrid {grid.id}"
            ))


    # ---------------------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------------------

    def get_point(self, lat, lon):
        """Get or create a Point with (lat, lon)."""
        p, _ = Point.objects.get_or_create(lat=lat, lon=lon)
        return p

    def update_region_corners(self, region, grid):
        """
        If zones already exist, still recompute region corners from center.
        This ensures region corner points are always correct.
        """

        corners = compute_region_corners(
            center_lat=region.center.lat,
            center_lon=region.center.lon,
            side_km=grid.side_km
        )

        A = self.get_point(*corners["A"])
        B = self.get_point(*corners["B"])
        C = self.get_point(*corners["C"])
        D = self.get_point(*corners["D"])

        region.A = A
        region.B = B
        region.C = C
        region.D = D
        region.save()

        self.stdout.write(self.style.SUCCESS(
            f"✔ Updated region corners for Region {region.id}"
        ))
