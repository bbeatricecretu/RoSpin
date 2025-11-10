from django.db import models


class Point(models.Model):
    """Represents a geographical coordinate (latitude, longitude)."""
    lat = models.FloatField()
    lon = models.FloatField()

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
    A = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_A")
    B = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_B")
    C = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_C")
    D = models.OneToOneField(Point, on_delete=models.SET_NULL, null=True, blank=True, related_name="region_D")

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

    def __str__(self):
        return f"Region @ {self.center}"


class Zone(models.Model):
    """Sub-zone inside a Region, with wind and terrain data."""
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="zones")

    A = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_A")
    B = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_B")
    C = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_C")
    D = models.OneToOneField(Point, on_delete=models.CASCADE, related_name="zone_D")

    min_alt = models.IntegerField(default=0)
    max_alt = models.IntegerField(default=0)
    roughness = models.IntegerField(default=0)
    air_density = models.FloatField(default=0.0)
    avg_wind_speed = models.FloatField(default=0.0)
    power_avg = models.FloatField(default=0.0)
    land_type = models.CharField(max_length=50, blank=True)
    potential = models.FloatField(default=0.0)

    infrastructure = models.OneToOneField(Infrastructure, on_delete=models.CASCADE)

    def __str__(self):
        return f"Zone of Region {self.region.id}"
