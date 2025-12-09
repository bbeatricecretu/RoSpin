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
        - wind_direction: Power-weighted prevailing direction 0-360° (0°=North)
    
    Why:
        - wind speed: primary driver of power generation (P ∝ v³)
        - 100m height: typical turbine hub height (80-120m)
        - wind direction: critical for turbine layout and wake optimization
          * Power-weighted to show where STRONG winds come from
          * Essential for minimizing wake losses (20-40% impact)
          * Determines turbine spacing (5-10 diameters in prevailing direction)

    Source: ERA5 u/v wind components at 100m height
    Resolution: ~25km (ERA5 coarser than ERA5-Land but has 100m data)
    
    Expected: 
        - Speed: 5-12 m/s at 100m for viable sites, >9 m/s excellent
        - Direction: Coastal sites (NE-E from sea), Inland (W-NW from Atlantic)

    Note: 
        - Speed calculated per-hour first to avoid cancellation (fixed bug)
        - Direction weighted by v³ to emphasize energy-producing winds
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

        z.min_alt = round(float(props.get("elevation_min") or 0.0), 2)
        z.max_alt = round(float(props.get("elevation_max") or 0.0), 2)
        z.roughness = round(float(props.get("tri_stdDev") or 0.0), 2)
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

        z.air_density = round(float(props.get("mean") or 0.0), 3)
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

        z.power_avg = round(float(props.get("mean") or 0.0), 1)
        z.save()


def compute_land_cover(zones, fc, zone_map):
    """
    STEP 6: Classify land cover type with percentages.
    
    Source: ESA WorldCover v200 (2021 data)
    Resolution: 10m
    
    What: All land cover classes in zone with their percentage coverage
    Result: Dict like {"Grassland": 45.2, "Cropland": 30.1, "Tree cover": 24.7}
    
    Classes: Tree cover, Shrubland, Grassland, Cropland, Built-up, 
             Bare/sparse, Snow/ice, Water, Wetland, Mangroves
    
    Why: Determines site suitability
        ✓ Suitable: Grassland, Cropland, Bare/sparse, Shrubland
        ✗ Excluded: Built-up, Water, Wetland, Snow/ice, Mangroves
    
    Method: Frequency histogram → calculate percentage for each class
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
            z.land_type = {}
            z.save()
            continue

        # Convert string keys to int and get counts
        hist_clean = {}
        for k, v in hist.items():
            try:
                class_id = int(float(k))
                count = float(v)
                hist_clean[class_id] = count
            except (ValueError, TypeError):
                continue

        if not hist_clean:
            z.land_type = {}
            z.save()
            continue

        # Calculate total pixels for percentage calculation
        total_pixels = sum(hist_clean.values())
        
        # Build dict with percentages for ALL classes (sorted by percentage descending)
        land_type_percentages = {}
        for class_id, count in hist_clean.items():
            label = WORLD_COVER_CLASSES.get(class_id, f"class_{class_id}")
            percentage = round((count / total_pixels) * 100, 1)
            land_type_percentages[label] = percentage
        
        # Sort by percentage descending
        z.land_type = dict(sorted(land_type_percentages.items(), key=lambda x: x[1], reverse=True))
        z.save()


# ---------------------------------------------------------
# LAND SUITABILITY SCORING
# ---------------------------------------------------------

# Suitability scores for each ESA WorldCover land class
# Scale: 0.0 (completely unsuitable) to 1.0 (ideal for wind farms)
LAND_SUITABILITY_SCORES = {
    "Grassland": 1.0,           # Open, ideal terrain
    "Bare / sparse": 1.0,       # Open, minimal vegetation
    "Cropland": 0.9,            # Generally usable, some constraints
    "Shrubland": 1.0,           # Open, suitable for development
    "Tree cover": 0.4,          # Clearing/environment issues, access difficulties
    "Moss / lichen": 0.4,       # Tundra-like, fragile soils
    "Built-up": 0.0,            # Hard exclusion - urban areas
    "Permanent water": 0.0,     # Hard exclusion - water bodies
    "Herbaceous wetland": 0.0,  # Hard exclusion - protected wetlands
    "Snow / ice": 0.0,          # Hard exclusion - permanent ice
    "Mangroves": 0.0,           # Hard exclusion - protected coastal
}

# Hard exclusion classes (score = 0.0)
HARD_EXCLUSION_CLASSES = {
    "Built-up",
    "Permanent water",
    "Herbaceous wetland",
    "Snow / ice",
    "Mangroves",
}


def compute_land_suitability(land_type_dict):
    """
    Calculate land suitability index from land cover composition.
    
    Args:
        land_type_dict: Dictionary of land types with percentages
                       e.g., {"Grassland": 45.2, "Cropland": 30.1, "Tree cover": 20.0, "Built-up": 4.7}
    
    Returns:
        tuple: (S_land, F_buildable)
            - S_land: Land suitability index [0-1] based on all land types
            - F_buildable: Fraction of zone that is buildable [0-1]
    
    Methodology:
        1. Calculate buildable fraction (area not in hard exclusion classes)
        2. Compute area-weighted suitability score over buildable area only
        3. No hard threshold - even zones with low buildable fraction get scored
    
    Formula:
        F_buildable = Σ(f_c) for c ∉ hard exclusion classes
        
        S_land = Σ(f_c × s_c) / F_buildable for c ∉ hard exclusion classes
        
    where:
        f_c = fractional area of class c (percentage / 100)
        s_c = suitability score for class c
        
    Note: Even if F_buildable is low (e.g., 20%), S_land will reflect that
          buildable portion's quality, and the low fraction naturally reduces
          the final potential through the weighted calculation.
    """
    if not land_type_dict:
        return 0.0, 0.0
    
    # Convert percentages to fractions
    total_fraction = 0.0
    buildable_fraction = 0.0
    weighted_suitability = 0.0
    
    for land_class, percentage in land_type_dict.items():
        fraction = percentage / 100.0  # Convert percentage to fraction
        total_fraction += fraction
        
        # Get suitability score (default to 0.5 for unknown classes)
        suitability = LAND_SUITABILITY_SCORES.get(land_class, 0.5)
        
        # Track buildable area (non-excluded classes)
        if land_class not in HARD_EXCLUSION_CLASSES:
            buildable_fraction += fraction
            weighted_suitability += fraction * suitability
    
    # Calculate land suitability index (normalized over buildable area)
    # If no buildable area, return 0
    if buildable_fraction > 0:
        S_land = weighted_suitability / buildable_fraction
    else:
        S_land = 0.0
    
    # Natural penalty: multiply by buildable fraction
    # This way 20% buildable with perfect land (S_land=1.0) gives 0.2 final contribution
    # More gradual than hard cutoff, but still heavily penalizes unsuitable zones
    S_land_effective = S_land * buildable_fraction
    
    return S_land_effective, buildable_fraction


def compute_potential(zones):
    """
    STEP 7: Calculate overall site suitability score with gradual land assessment.
    
    Formula: potential = 100 × S_base × S_land_effective
    
    Where:
        S_base = 0.7 × S_wind + 0.3 × S_terrain
        
        S_wind = min(1.25, power_avg / 800)  [normalized wind power density]
        S_terrain = 1 - min(1.0, roughness / 50)  [terrain smoothness: 1=flat, 0=rough]
        
        S_land_effective = (S_land_quality × F_buildable)
        S_land_quality = weighted suitability of buildable area [0-1]
        F_buildable = fraction of buildable land [0-1]
    
    Land Suitability Approach:
        - Each land cover class has a suitability score s_c ∈ [0,1]
        - Hard exclusion classes (urban, water, wetlands) have s_c = 0
        - S_land_quality reflects quality of buildable portion
        - F_buildable naturally penalizes zones with much excluded land
        - NO hard threshold - even 20% buildable zones get low but non-zero score
    
    Example:
        Zone A: 80% water, 20% grassland (perfect buildable land)
        - S_land_quality = 1.0 (grassland is perfect)
        - F_buildable = 0.2
        - S_land_effective = 1.0 × 0.2 = 0.2
        - If S_base = 0.8, then potential = 100 × 0.8 × 0.2 = 16.0 (Poor, but not 0)
        
        Zone B: 50% water, 50% grassland
        - S_land_effective = 1.0 × 0.5 = 0.5
        - If S_base = 0.8, then potential = 100 × 0.8 × 0.5 = 40.0 (Marginal)
    
    Interpretation:
        - 0-20: Poor (red) - Not viable for development
        - 20-40: Marginal (orange) - Low viability
        - 40-70: Fair (yellow) - Moderate potential
        - 70-100: Good (green) - High development potential
    
    Component Weights:
        - Wind resource: 70% (primary driver)
        - Terrain: 30% (construction feasibility)
        - Land: multiplicative factor (site-specific constraints, gradual penalty)
    """
    for z in zones:
        # Wind component (normalized wind power density)
        wpd = (z.power_avg or 0.0) / 800
        S_wind = min(1.25, wpd)  # Cap at 1.25 for exceptional sites
        
        # Terrain component (smoothness score)
        S_terrain = 1 - min(1.0, (z.roughness or 0.0) / 50)
        
        # Land suitability component (gradual, no hard cutoff)
        land_types = z.land_type if isinstance(z.land_type, dict) else {}
        S_land_effective, F_buildable = compute_land_suitability(land_types)
        
        # Base score (wind + terrain)
        S_base = 0.7 * S_wind + 0.3 * S_terrain
        
        # Final potential (base score modulated by land suitability)
        # S_land_effective already includes buildable fraction penalty
        z.potential = round(100 * S_base * S_land_effective, 1)
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
