import ee
from analysis.models import Zone, RegionGrid
from analysis.core.gee_data import (
    get_avg_temperature,
    get_avg_wind_speeds,
    get_dem_layers,
    get_air_density_image,
    get_wind_power_density_image,
    get_landcover_image,
    WORLD_COVER_CLASSES,
)
from analysis.core.wind import compute_wind_rose


EXCLUDED_LAND = {
    "Built-up",
    "Permanent water",
    "Herbaceous wetland",
    "Snow / ice",
    "Mangroves",
}


def compute_temperature(region):
    """
    STEP 1: Compute average annual temperature at region center.
    
    Source: ERA5-Land Hourly Reanalysis (ECMWF)
    Resolution: ~11km (1000m scale)
    
    What: Mean 2m air temperature over full year (°C)
    Why: Affects air density calculation and equipment performance
    Expected: -50°C to +50°C depending on location
    """ 
    temp = get_avg_temperature(region.center.lat, region.center.lon)
    region.avg_temperature = temp
    region.save()
    return temp


def compute_wind_per_zone(zones):
    """
    STEP 2: Compute wind speed and direction for each zone.
    
    Source: ERA5-Land u/v wind components at 10m height
    Resolution: ~11km (1000m scale)
    
    What: 
        - avg_wind_speed: √(u² + v²) averaged over year (m/s)
        - wind_direction: Meteorological direction 0-360° (0°=North)
    
    Why: Primary driver of power generation (P ∝ v³)
    Expected: 3-8 m/s for viable sites, >6 m/s excellent
    
    Note: Speed calculated per-hour first to avoid cancellation (fixed bug)
    """
    centers = []
    for z in zones:
        lat = round((z.A.lat + z.B.lat + z.C.lat + z.D.lat) / 4, 5)
        lon = round((z.A.lon + z.B.lon + z.C.lon + z.D.lon) / 4, 5)
        centers.append((lat, lon))

    wind_data = get_avg_wind_speeds(centers)

    for z, (lat, lon) in zip(zones, centers):
        data = wind_data.get((lat, lon))
        if not data:
            z.avg_wind_speed = 0.0
            z.wind_direction = 0.0
        else:
            z.avg_wind_speed = round(data["speed"], 2)
            z.wind_direction = round(data["direction"], 1)
        z.save()


def compute_altitude_roughness_dem(zones, fc, zone_map):
    """
    STEP 3: Compute terrain metrics from Digital Elevation Model.
    
    Source: Copernicus GLO-30 DEM
    Resolution: 30m
    
    What:
        - min_alt: Minimum elevation in zone (meters above sea level)
        - max_alt: Maximum elevation in zone (meters)
        - roughness: Terrain Ruggedness Index (TRI) = std dev of elevation
    
    Why:
        - Altitude affects air density (higher = thinner air = less power)
        - Roughness indicates turbulent flow (>20 = poor performance)
        - Flat terrain (roughness <5) = ideal for turbines
    
    Expected:
        - Altitude: 0-3000m for most sites
        - Roughness: 0-5 flat, 5-20 gentle hills, >50 mountains
    """
    dem_img = get_dem_layers()
    reducer = (
        ee.Reducer.mean()
        .combine(ee.Reducer.minMax(), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True)
    )

    dem = dem_img.reduceRegions(fc, reducer, scale=30).getInfo()

    for f in dem["features"]:
        props = f["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        z.min_alt = round(float(props.get("elevation_min", 0.0)), 2)
        z.max_alt = round(float(props.get("elevation_max", 0.0)), 2)
        z.roughness = round(float(props.get("tri_stdDev", 0.0)), 2)
        z.save()


def compute_air_density(zones, fc, zone_map):
    """
    STEP 4: Compute air density using ideal gas law.
    
    Source: ERA5-Land surface pressure & 2m temperature
    Resolution: ~11km (1000m scale)
    Formula: ρ = P / (R_d × T)
        - P: surface pressure (Pa)
        - T: temperature (K)
        - R_d: 287.05 J/(kg·K) - dry air constant
    
    What: Air density in kg/m³
    Why: Directly affects power output (P = 0.5 × ρ × v³ × A)
    
    Expected:
        - Sea level: ~1.225 kg/m³
        - 1000m: ~1.06-1.10 kg/m³
        - 2000m: ~0.95 kg/m³
        - Higher altitude = lower density = less power
    """
    img = get_air_density_image()
    air = img.reduceRegions(fc, ee.Reducer.mean(), scale=1000).getInfo()

    for f in air["features"]:
        props = f["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        z.air_density = round(float(props.get("mean", 0.0)), 3)
        z.save()


def compute_power_density(zones, fc, zone_map):
    """
    STEP 5: Compute wind power density.
    
    Source: ERA5-Land wind components + calculated air density
    Resolution: ~11km (1000m scale)
    Formula: P = 0.5 × ρ × v³ (Betz's law)
    
    What: Available wind power per square meter (W/m²)
    Why: Key metric for site viability - predicts energy production
    
    Wind Power Classes:
        - <100 W/m²: Poor (Class 1)
        - 100-150: Marginal (Class 2)
        - 150-200: Fair (Class 3)
        - 200-400: Good (Class 4-5)
        - >400: Excellent (Class 6-7)
    
    Note: Calculated per-hour then averaged to preserve cubic relationship
    """
    img = get_wind_power_density_image()
    pw = img.reduceRegions(fc, ee.Reducer.mean(), scale=1000).getInfo()

    for f in pw["features"]:
        props = f["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        z.power_avg = round(float(props.get("mean", 0.0)), 1)
        z.save()


def compute_land_cover(zones, fc, zone_map):
    """
    STEP 6: Classify land cover type.
    
    Source: ESA WorldCover v200 (2021 data)
    Resolution: 10m
    
    What: Dominant land cover class(es) in zone
    Classes: Tree cover, Shrubland, Grassland, Cropland, Built-up, 
             Bare/sparse, Snow/ice, Water, Wetland, Mangroves
    
    Why: Determines site suitability
        ✓ Suitable: Grassland, Cropland, Bare/sparse, Shrubland
        ✗ Excluded: Built-up, Water, Wetland, Snow/ice, Mangroves
    
    Method: Frequency histogram → most common class(es)
    Note: Fixed string-to-int conversion bug for accurate matching
    """
    img = get_landcover_image()
    lc = img.reduceRegions(fc, ee.Reducer.frequencyHistogram(), scale=10).getInfo()

    for feat in lc["features"]:
        props = feat["properties"]
        z = zone_map.get(int(props["zone_id"]))
        if not z:
            continue

        hist = props.get("histogram")
        if not hist:
            z.land_type = ""
            z.save()
            continue

        # Fixed: Convert string keys to int before comparison
        hist_clean = {}
        for k, v in hist.items():
            try:
                class_id = int(float(k))
                count = float(v)
                hist_clean[class_id] = count
            except (ValueError, TypeError):
                continue

        if not hist_clean:
            z.land_type = ""
            z.save()
            continue

        max_count = max(hist_clean.values())
        dom_classes = [cid for cid, cnt in hist_clean.items() if cnt == max_count]
        labels = [WORLD_COVER_CLASSES.get(c, f"class_{c}") for c in dom_classes]

        z.land_type = ", ".join(labels)
        z.save()


def compute_potential(zones):
    """
    STEP 7: Calculate overall site suitability score.
    
    Formula: potential = 100 × (0.7 × wpd_norm + 0.3 × roughness_penalty) × land_ok
    
    Where:
        - wpd_norm = min(1.25, power_avg / 800)  [0-1.25 scale]
        - roughness_penalty = 1 - min(1.0, roughness / 50)  [1=flat, 0=rough]
        - land_ok = 0 if excluded land type, else 1
    
    What: Final score 0-100
    Why: Combines all factors into single ranking metric
    
    Interpretation:
        - 0-20: Poor (red) - Not viable
        - 20-40: Marginal (orange) - Low viability
        - 40-70: Fair (yellow) - Moderate potential
        - 70-100: Good (green) - High potential
    
    Weights: 70% power density, 30% terrain smoothness
    """
    for z in zones:
        wpd = (z.power_avg or 0.0) / 800
        wpd = min(1.25, wpd)
        rough = 1 - min(1.0, (z.roughness or 0.0) / 50)
        ok_land = 0 if z.land_type in EXCLUDED_LAND else 1

        z.potential = round(100 * (0.7 * wpd + 0.3 * rough) * ok_land, 1)
        z.save()


def compute_region_metrics(region, zones):
    """
    STEP 8: Aggregate zone data to region level.
    
    What:
        - wind_rose: Distribution of wind directions (JSON)
        - avg_potential: Mean potential score across all zones
        - rating: Integer rating (0-1000) = avg_potential × 10
    
    Why: Provides region-wide summary for quick comparison
    
    Wind Rose: Shows predominant wind patterns for region
    Rating: Single number for ranking regions (higher = better)
    """
    region.wind_rose = compute_wind_rose(zones)
    region.avg_potential = sum(z.potential for z in zones) / len(zones)
    region.rating = int(region.avg_potential * 10)
    region.save()


def compute_gee_for_grid(grid: RegionGrid):
    """
    FULL 8-STEP PIPELINE: Fetch all Google Earth Engine data for a grid.
    
    Process:
        1. Temperature (region center)
        2. Wind speed & direction (per zone)
        3. DEM terrain metrics (per zone)
        4. Air density (per zone)
        5. Wind power density (per zone)
        6. Land cover classification (per zone)
        7. Potential scoring (per zone)
        8. Region-level aggregation
    
    This ensures API returns identical values to fetch_gee_data command.
    """
    region = grid.region
    zones = list(grid.zones.all())

    if not zones:
        return

    # Step 1: Temperature
    compute_temperature(region)

    # Step 2: Wind
    compute_wind_per_zone(zones)

    # Build FeatureCollection for spatial operations
    zone_map = {z.id: z for z in zones}
    features = []
    for z in zones:
        poly = [
            [z.A.lon, z.A.lat],
            [z.B.lon, z.B.lat],
            [z.C.lon, z.C.lat],
            [z.D.lon, z.D.lat],
            [z.A.lon, z.A.lat],
        ]
        features.append(ee.Feature(
            ee.Geometry.Polygon([poly]),
            {"zone_id": z.id}
        ))
    fc = ee.FeatureCollection(features)

    # Steps 3-6: Spatial computations
    compute_altitude_roughness_dem(zones, fc, zone_map)
    compute_air_density(zones, fc, zone_map)
    compute_power_density(zones, fc, zone_map)
    compute_land_cover(zones, fc, zone_map)

    # Step 7: Potential scoring
    compute_potential(zones)

    # Step 8: Region aggregation
    compute_region_metrics(region, zones)
