from django.db import models


# ---------------------------------------------------------
# POINT MODEL
# ---------------------------------------------------------

class Point(models.Model):
    """
    Represents a geographical coordinate (latitude, longitude),
    used for region corners and zone corners.
    """
    lat = models.FloatField()
    lon = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lat", "lon"], name="unique_lat_lon")
        ]

    def __str__(self):
        return f"({self.lat:.5f}, {self.lon:.5f})"


# ---------------------------------------------------------
# INFRASTRUCTURE MODEL
# ---------------------------------------------------------

class Infrastructure(models.Model):
    """
    Represents infrastructure proximity such as roads, highways, etc.
    You can expand this later with more detailed scoring.
    """
    index = models.IntegerField(default=0)
    km_jud = models.IntegerField(default=0)
    km_nat = models.IntegerField(default=0)
    km_euro = models.IntegerField(default=0)
    km_auto = models.IntegerField(default=0)

    def __str__(self):
        return f"Infrastructure #{self.index}"


# ---------------------------------------------------------
# ENERGY STORAGE MODEL
# ---------------------------------------------------------

class EnergyStorage(models.Model):
    """
    Optional: nearby hydro, battery or grid storage facilities.
    Not central now but useful for future analysis.
    """
    name = models.CharField(max_length=100)
    coordinates = models.OneToOneField(Point, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# ---------------------------------------------------------
# REGION MODEL
# ---------------------------------------------------------

class Region(models.Model):
    """
    Represents a high-level analysis region (20×20 km or otherwise),
    with geometry (center + corners) and aggregated metrics.
    """

    center = models.ForeignKey(
        Point, on_delete=models.CASCADE, related_name="region_center"
    )

    # Region corners (A=NE, B=SE, C=SW, D=NW) - ForeignKey allows sharing
    A = models.ForeignKey(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_A")
    B = models.ForeignKey(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_B")
    C = models.ForeignKey(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_C")
    D = models.ForeignKey(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_D")

    # Region-level aggregated metrics
    avg_temperature = models.FloatField(default=0.0)
    wind_rose = models.JSONField(default=dict, blank=True)
    rating = models.IntegerField(default=0)

    # Zone-related metrics
    max_potential = models.ForeignKey(
        'Zone', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="max_in_region"
    )
    avg_potential = models.FloatField(default=0.0)
    infrastructure_rating = models.FloatField(default=0.0)
    index_average = models.FloatField(default=0.0)

    closest_storage = models.ForeignKey(
        EnergyStorage, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        pass

    def __str__(self):
        return f"Region #{self.id} @ ({self.center.lat:.4f}, {self.center.lon:.4f})"


# ---------------------------------------------------------
# REGION GRID MODEL
# ---------------------------------------------------------

class RegionGrid(models.Model):
    """
    A specific grid resolution for a region (e.g. 10×10, 20×20).
    Each grid stores its own corners (optional).
    """

    region = models.ForeignKey(
        Region, on_delete=models.CASCADE, related_name="grids"
    )
    side_km = models.FloatField()           # e.g. 20 km
    zones_per_edge = models.IntegerField()  # e.g. 10

    # Optional: store computed corners of the grid
    A = models.ForeignKey(Point, null=True, blank=True, on_delete=models.SET_NULL, related_name="grid_A")
    B = models.ForeignKey(Point, null=True, blank=True, on_delete=models.SET_NULL, related_name="grid_B")
    C = models.ForeignKey(Point, null=True, blank=True, on_delete=models.SET_NULL, related_name="grid_C")
    D = models.ForeignKey(Point, null=True, blank=True, on_delete=models.SET_NULL, related_name="grid_D")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["region", "side_km", "zones_per_edge"],
                name="unique_region_grid_config",
            )
        ]

    def __str__(self):
        return f"Grid {self.id} for Region {self.region.id} ({self.zones_per_edge}×{self.zones_per_edge})"


# ---------------------------------------------------------
# ZONE MODEL
# ---------------------------------------------------------

class Zone(models.Model):
    """
    A 2×2 km (or similar) sub-zone inside a RegionGrid.
    Stores geometry, wind data, DEM, classification and potential.
    """

    grid = models.ForeignKey(
        RegionGrid, on_delete=models.CASCADE, related_name="zones"
    )

    # Geometry (corner points) - ForeignKey allows multiple zones to share points
    A = models.ForeignKey(Point, on_delete=models.CASCADE, related_name="zone_A")
    B = models.ForeignKey(Point, on_delete=models.CASCADE, related_name="zone_B")
    C = models.ForeignKey(Point, on_delete=models.CASCADE, related_name="zone_C")
    D = models.ForeignKey(Point, on_delete=models.CASCADE, related_name="zone_D")

    # Wind
    wind_direction = models.FloatField(default=0.0)  # degrees 0–360
    avg_wind_speed = models.FloatField(default=0.0)  # m/s

    # DEM / Terrain
    min_alt = models.FloatField(default=0.0)
    max_alt = models.FloatField(default=0.0)
    roughness = models.FloatField(default=0.0)

    # Air & Power
    air_density = models.FloatField(default=0.0)
    power_avg = models.FloatField(default=0.0)  # W/m²

    # Classification
    land_type = models.CharField(max_length=50, blank=True)
    potential = models.FloatField(default=0.0)

    # Index inside the grid (1→100)
    zone_index = models.IntegerField(default=0)

    # Infrastructure
    infrastructure = models.ForeignKey(
        Infrastructure, on_delete=models.CASCADE
    )

    def __str__(self):
        return (
            f"Region {self.grid.region.id} | Grid {self.grid.id} | Zone {self.zone_index}"
        )

    @property
    def center(self):
        """Return center (lat, lon) of the zone."""
        return (
            (self.A.lat + self.B.lat + self.C.lat + self.D.lat) / 4,
            (self.A.lon + self.B.lon + self.C.lon + self.D.lon) / 4,
        )