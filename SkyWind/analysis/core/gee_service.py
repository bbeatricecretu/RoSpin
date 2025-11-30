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


'''
# ---------------------------------------------------------
!!! gee_service use gee_data and wind
# ---------------------------------------------------------
ZONE:
    - wind direction -> compute_wind_per_zone()
    - avg_wind_speed -> compute_wind_per_zone()
    - min_alt, max_alt, roughness -> compute_altitude_roughness_dem()
    - air_density -> compute_air_density()
    - power_avg -> compute_WIND_power_density()
    - land_type -> compute_land_cover()
    - potential -> compute_potential()

REGION:
    - avg_temperature -> compute_temperature()
    - wind_rose -> compute_region_metrics()
    - rating -> compute_region_metrics() ---> renuntat la unul dintre ele
    - avg_potential -> compute_region_metrics() ---> renuntat la unul dintre ele
    - most_suitable_energy_storage -> (not implemented)
'''

# ---------------------------------------------------------
# ZONE ATTRIBUTES
# ---------------------------------------------------------

def compute_wind_per_zone(zones):
    """
    STEP 2: Compute wind speed and direction for each zone.
    
    What: 
        - avg_wind_speed: Wind speed at 100m height (m/s) - direct from ERA5
        - wind_direction: Meteorological direction 0-360° (0°=North)
    
    Why:
        - wind speed: primary driver of power generation (P ∝ v³)
        - 100m height: typical turbine hub height (80-120m)
        - wind direction: important for turbine alignment and layout

    Source: ERA5 u/v wind components at 100m height
    Resolution: ~25km (ERA5 coarser than ERA5-Land but has 100m data)
    
    Expected: 5-12 m/s at 100m for viable sites, >9 m/s excellent

    Note: 
        - Speed calculated per-hour first to avoid cancellation (fixed bug)
        - ERA5 directly provides 100m wind (no extrapolation needed)
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
            # ERA5 already gives us annual mean wind at 100m
            v100 = float(data.get("speed", 0.0) or 0.0)

            # Store the 100m value directly (no scaling needed)
            z.avg_wind_speed = round(v100, 2)

            # Keep direction as-is (height doesn't change mean direction much)
            z.wind_direction = round(float(data.get("direction", 0.0) or 0.0), 1)
        z.save()


def compute_altitude_roughness_dem(zones, fc, zone_map):
    """
    STEP 3: Compute terrain metrics from Digital Elevation Model.
    
    What:
        - min_alt: Minimum elevation in zone (meters above sea level)
        - max_alt: Maximum elevation in zone (meters)
        - roughness: Terrain Ruggedness Index (TRI) = std dev of elevation
    
    Why:
        - Altitude affects air density (higher = thinner air = less power)
        - Roughness indicates turbulent flow (>20 = poor performance)
        - Flat terrain (roughness <5) = ideal for turbines
            
    Source: Copernicus GLO-30 DEM
    Resolution: 30m
    
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

    What: Air density in kg/m³
    Why: Directly affects power output (P = 0.5 × ρ × v³ × A)
    
    Source: ERA5-Land surface pressure & 2m temperature
    Resolution: ~11km (1000m scale)
    Formula: ρ = P / (R_d × T)
        - P: surface pressure (Pa)
        - T: temperature (K)
        - R_d: 287.05 J/(kg·K) - dry air constant
    
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


def compute_WIND_power_density(zones, fc, zone_map):
    """
    STEP 5: Compute wind power density.
     
    What: Available wind power per square meter (W/m²)
    Why: Key metric for site viability - predicts energy production
    
    Source: ERA5 100m wind + ERA5-Land surface pressure/temperature
    Resolution: ~25km for wind, ~11km for surface data
    Formula: P = 0.5 × ρ × v³ (Betz's law)
    
    Wind Power Classes (at 100m height):
        - <300 W/m²: Poor (Class 1)
        - 300-500: Marginal (Class 2)
        - 500-800: Fair (Class 3)
        - 800-1200: Good (Class 4-5)
        - >1200: Excellent (Class 6-7)
    
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


EXCLUDED_LAND = {
    "Built-up",
    "Permanent water",
    "Herbaceous wetland",
    "Snow / ice",
    "Mangroves",
}

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

# ---------------------------------------------------------
# REGION ATTRIBUTES
# ---------------------------------------------------------

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

# ---------------------------------------------------------
# FULL PIPELINE
# ---------------------------------------------------------
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
    compute_WIND_power_density(zones, fc, zone_map)
    compute_land_cover(zones, fc, zone_map)

    # Step 7: Potential scoring
    compute_potential(zones)

    # Step 8: Region aggregation
    compute_region_metrics(region, zones)
