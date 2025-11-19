from django.db import models


class Point(models.Model):
    """Represents a geographical coordinate (latitude, longitude)."""
    lat = models.FloatField()
    lon = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lat", "lon"], name="unique_lat_lon")
        ]

    def __str__(self):
        return f"({self.lat:.4f}, {self.lon:.4f})"


class Infrastructure(models.Model):
    """Describes infrastructure proximity: roads, highways, etc."""
    index = models.IntegerField(default=0)
    km_jud = models.IntegerField(default=0)
    km_nat = models.IntegerField(default=0)
    km_euro = models.IntegerField(default=0)
    km_auto = models.IntegerField(default=0)

    def __str__(self):
        return f"Infrastructure #{self.index}"


class EnergyStorage(models.Model):
    """Represents an energy storage facility (hydro, battery, etc.)."""
    name = models.CharField(max_length=100)
    coordinates = models.OneToOneField(Point, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Region(models.Model):
    """Defines a geographical region (the main analysis area)."""

    center = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="region_center")

    # Corners of the region
    A = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_A")
    B = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_B")
    C = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_C")
    D = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_D")

    # Region-level aggregated metrics
    avg_temperature = models.FloatField(default=0.0)
    wind_rose = models.JSONField(default=list, blank=True)
    rating = models.IntegerField(default=0)

    max_potential = models.ForeignKey(
        'Zone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='max_in_region'
    )

    avg_potential = models.FloatField(default=0.0)
    closest_storage = models.ForeignKey(EnergyStorage, on_delete=models.SET_NULL, null=True, blank=True)
    infrastructure_rating = models.IntegerField(default=0)
    index_average = models.FloatField(default=0.0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["center"], name="unique_region_center")
        ]

    def __str__(self):
        return f"Region @ {self.center}"

    # ---------------------------------------------------------
    # WIND ROSE COMPUTATION
    # ---------------------------------------------------------

    def compute_wind_rose(self, grid=None):
        """Compute average wind speed per direction (N, NE, E, SE, S, SW, W, NW)."""

        if grid is None:
            grid = self.grids.order_by('-zones_per_edge').first()

        if grid is None:
            self.wind_rose = {}
            self.save()
            return

        zones = list(grid.zones.all())
        if not zones:
            self.wind_rose = {}
            self.save()
            return

        bins = {
            "N": [], "NE": [], "E": [], "SE": [],
            "S": [], "SW": [], "W": [], "NW": []
        }

        def sector(deg):
            if deg < 0:
                deg += 360
            if 337.5 <= deg or deg < 22.5: return "N"
            if 22.5 <= deg < 67.5: return "NE"
            if 67.5 <= deg < 112.5: return "E"
            if 112.5 <= deg < 157.5: return "SE"
            if 157.5 <= deg < 202.5: return "S"
            if 202.5 <= deg < 247.5: return "SW"
            if 247.5 <= deg < 292.5: return "W"
            if 292.5 <= deg < 337.5: return "NW"

        # bucket zones
        for z in zones:
            d = sector(z.wind_direction)
            bins[d].append(z.avg_wind_speed)

        # compute averages
        rose = {
            k: (sum(v) / len(v) if v else 0.0)
            for k, v in bins.items()
        }

        self.wind_rose = rose
        self.save()

    # ---------------------------------------------------------
    # REGION METRICS FROM ZONES
    # ---------------------------------------------------------

    def compute_from_zones(self, grid=None):
        """Compute region-level metrics from ALL zones in the grid"""

        if grid is None:
            grid = self.grids.order_by('-zones_per_edge').first()
            if grid is None:
                return

        zones = list(grid.zones.all())
        if not zones:
            return

        self.avg_potential = sum(z.potential for z in zones) / len(zones)
        self.max_potential = max(zones, key=lambda z: z.potential)
        self.infrastructure_rating = sum(z.infrastructure.index for z in zones) / len(zones)
        self.index_average = sum(z.zone_index for z in zones) / len(zones)

        # simple rating formula
        self.rating = int(self.avg_potential * 10)

        # compute wind rose afterwards
        self.compute_wind_rose(grid)
        self.save()

class RegionGrid(models.Model):
    """
    A specific grid configuration for a Region.
    Same region, but different resolution or side km.
    """

    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="grids")
    side_km = models.FloatField()
    zones_per_edge = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["region", "side_km", "zones_per_edge"],
                name="unique_region_grid_config"
            )
        ]

    def __str__(self):
        return f"Grid for Region {self.region.id} ({self.zones_per_edge}x{self.zones_per_edge}, {self.side_km} km)"


class Zone(models.Model):
    """Sub-zone inside a RegionGrid."""

    grid = models.ForeignKey(RegionGrid, on_delete=models.CASCADE, related_name="zones")

    # geometry
    A = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_A")
    B = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_B")
    C = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_C")
    D = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_D")

    # wind
    wind_direction = models.FloatField(default=0.0)
    avg_wind_speed = models.FloatField(default=0.0)

    # DEM / Terrain
    min_alt = models.IntegerField(default=0)
    max_alt = models.IntegerField(default=0)
    roughness = models.IntegerField(default=0)

    # Air & Power
    air_density = models.FloatField(default=0.0)
    power_avg = models.FloatField(default=0.0)

    # Classification + index
    land_type = models.CharField(max_length=50, blank=True)
    potential = models.FloatField(default=0.0)
    zone_index = models.IntegerField(default=0)

    # foreign key
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)

    def __str__(self):
        return f"Region {self.grid.region.id} – Grid {self.grid.id} – Zone {self.zone_index}"
