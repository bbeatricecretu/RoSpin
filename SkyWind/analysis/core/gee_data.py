import ee

# Initialize Earth Engine once
ee.Initialize(project='rospin1')


# ---------------------------------------------------------
# TEMPERATURE
# ---------------------------------------------------------

def get_avg_temperature(lat: float, lon: float, year: int = 2022) -> float:
    """
    REGION:
    Return mean annual 2m air temperature (°C) from ERA5-Land.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        year: Year for data retrieval (default: 2022)

    Returns:
        float: Mean annual temperature in Celsius, rounded to 2 decimals

    Notes:
        - Uses ERA5-Land hourly reanalysis data
        - Converts from Kelvin to Celsius: T(°C) = T(K) - 273.15
        - Averages all hourly values within 1km radius
        - Typical range: -50°C to +50°C
    """
    coll = (
        ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        .select('temperature_2m')
        .filterDate(f'{year}-01-01', f'{year}-12-31')
    )

    img = coll.mean()
    point = ee.Geometry.Point([lon, lat])

    kelvin = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=1000
    ).get('temperature_2m')

    return round(float(kelvin.getInfo()) - 273.15, 2)


# ---------------------------------------------------------
# WIND SPEED + WIND DIRECTION
# ---------------------------------------------------------

def get_avg_wind_speeds(centers, year: int = 2022):
    """
    ZONE:
    Fetch average annual wind speed and direction for multiple points.

    Args:
        centers: list of (lat, lon) tuples — already rounded to ~5 decimals
        year: year for data (default: 2022)

    Returns:
        dict[(lat, lon)] = {"speed": m/s, "direction": degrees (0–360)}

    Notes:
        - Uses ERA5-Land hourly data at 10m height
        - Speed: √(u² + v²) averaged over the year
        - Direction: meteorological (0° = North, 90° = East)
        - Returns 0.0 for missing data points
        - Resolution: ~11km (1000m scale)
    """

    if not centers:
        return {}

    coll = (
        ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        .select(['u_component_of_wind_10m', 'v_component_of_wind_10m'])
        .filterDate(f'{year}-01-01', f'{year}-12-31')
    )

    # FIXED: Calculate speed per hour FIRST, then average
    def calc_speed(img):
        """Calculate wind speed for each hourly image."""
        u = img.select('u_component_of_wind_10m')
        v = img.select('v_component_of_wind_10m')
        speed_img = u.pow(2).add(v.pow(2)).sqrt().rename('wind_speed')
        return img.addBands(speed_img)

    coll_with_speed = coll.map(calc_speed)
    
    # Average the speeds (not the components)
    speed = coll_with_speed.select('wind_speed').mean()

    # For direction, use mean components (this is acceptable for direction)
    mean_components = coll.mean()
    direction = mean_components.expression(
        '(180 / 3.14159265) * atan2(v, u)',
        {
            'u': mean_components.select('u_component_of_wind_10m'),
            'v': mean_components.select('v_component_of_wind_10m'),
        }
    ).rename('wind_dir')

    # Normalize to 0–360
    direction = direction.expression(
        '(dir + 360) % 360',
        {'dir': direction}
    )

    img = speed.addBands(direction)

    # Build FeatureCollection with index for better tracking
    feats = [
        ee.Feature(
            ee.Geometry.Point([lon, lat]),
            {
                'lat_key': lat,
                'lon_key': lon,
                'point_index': i
            }
        )
        for i, (lat, lon) in enumerate(centers)
    ]

    fc = ee.FeatureCollection(feats)

    reduced = img.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=1000
    ).getInfo()

    result = {}
    returned_count = 0

    for f in reduced['features']:
        p = f['properties']
        lat_key = p.get('lat_key')
        lon_key = p.get('lon_key')
        spd = p.get('wind_speed')
        direc = p.get('wind_dir')

        if lat_key is None or lon_key is None:
            continue

        returned_count += 1
        result[(float(lat_key), float(lon_key))] = {
            'speed': float(spd) if spd is not None else 0.0,
            'direction': float(direc) if direc is not None else 0.0,
        }

    # Warn if some points are missing
    if returned_count < len(centers):
        missing = len(centers) - returned_count
        print(f"⚠ Wind speed: {missing}/{len(centers)} points returned no data")

    return result


# ---------------------------------------------------------
# ROUGHNESS -> DEM (Elevation, Slope, Tri)
# ---------------------------------------------------------

def get_dem_layers():
    """
    ZONE:
    Create multi-band Earth Engine image with elevation, slope, and terrain roughness.

    Returns:
        ee.Image: Three-band image containing:
            - elevation: Height above sea level in meters
            - slope: Terrain slope in degrees (0-90°)
            - tri: Terrain Ruggedness Index (std dev in 11×11 window)

    Notes:
        - Source: Copernicus GLO-30 DEM (30m resolution)
        - TRI calculation: Standard deviation of elevation in 5-pixel radius
        - Use with reduceRegions() for zone-level statistics
    """
    dem = (
        ee.ImageCollection("COPERNICUS/DEM/GLO30")
        .mosaic()
        .select("DEM")
        .rename("elevation")
    )

    slope = ee.Terrain.slope(dem).rename("slope")

    tri = dem.reduceNeighborhood(
        reducer=ee.Reducer.stdDev(),
        kernel=ee.Kernel.square(radius=5, units="pixels")  # 11x11 window
    ).rename("tri")

    return dem.addBands([slope, tri])


# ---------------------------------------------------------
# AIR DENSITY ρ = p / (R_d * T)
# ---------------------------------------------------------

def get_air_density_image(year: int = 2022):
    """
    ZONE:
    Create Earth Engine image of air density using ideal gas law.

    Args:
        year: Year for data retrieval (default: 2022)

    Returns:
        ee.Image: Single-band image with air density in kg/m³

    Notes:
        - Formula: ρ = P / (R_d × T)
        - P: surface pressure (Pa) from ERA5-Land
        - T: 2m temperature (K) from ERA5-Land
        - R_d: specific gas constant for dry air = 287.05 J/(kg·K)
        - Typical values: 1.0-1.3 kg/m³ (sea level ≈ 1.225 kg/m³)
        - Calculates density per-hour then averages (consistent with wind speed method)
    """
    coll = (
        ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        .filterDate(f'{year}-01-01', f'{year}-12-31')
        .select(['surface_pressure', 'temperature_2m'])
    )

    # Calculate air density for each hour, then average
    def calc_density(img):
        """Calculate air density for each hourly image."""
        T = img.select('temperature_2m')  # Kelvin
        P = img.select('surface_pressure')  # Pascals
        R_d = 287.05
        rho = P.divide(T.multiply(R_d)).rename('air_density')
        return rho

    hourly_rho = coll.map(calc_density)
    return hourly_rho.mean()


# ---------------------------------------------------------
# WIND POWER DENSITY
# P = 0.5 * ρ * v³
# ---------------------------------------------------------

def get_wind_power_density_image(year: int = 2022):
    """
    ZONE:
    Create Earth Engine image of wind power density.

    Args:
        year: Year for data retrieval (default: 2022)

    Returns:
        ee.Image: Single-band image with wind power density in W/m²

    Notes:
        - Formula: P = 0.5 × ρ × v³ (per Betz's law)
        - Calculates power density for each hour, then averages
        - This preserves the cubic relationship of wind speed
        - Wind class guidelines:
            < 100 W/m²: Poor
            100-200 W/m²: Marginal
            200-300 W/m²: Fair
            300-400 W/m²: Good
            > 400 W/m²: Excellent
    """
    coll = (
        ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        .filterDate(f'{year}-01-01', f'{year}-12-31')
        .select([
            'u_component_of_wind_10m',
            'v_component_of_wind_10m',
            'surface_pressure',
            'temperature_2m'
        ])
    )

    def per_hour(img):
        u = img.select('u_component_of_wind_10m')
        v = img.select('v_component_of_wind_10m')
        T = img.select('temperature_2m')  # K
        P = img.select('surface_pressure')  # Pa
        R_d = 287.05

        speed = u.pow(2).add(v.pow(2)).sqrt()
        rho = P.divide(T.multiply(R_d))
        pd = rho.multiply(speed.pow(3)).multiply(0.5).rename('power_density')
        return pd

    hourly_pd = coll.map(per_hour)
    return hourly_pd.mean().rename('power_density')


# ---------------------------------------------------------
# LAND COVER
# ---------------------------------------------------------

def get_landcover_image(year: int = 2021):
    """
    ZONE:
    Load ESA WorldCover land cover classification image.

    Args:
        year: Year for land cover data (default: 2021)
              Note: ESA WorldCover v200 is only available for 2020 and 2021

    Returns:
        ee.Image: Single-band categorical image with land cover classes

    Notes:
        - Source: ESA WorldCover v200
        - Resolution: 10m
        - Use with frequencyHistogram() reducer to get class distribution
        - Class values map to WORLD_COVER_CLASSES dictionary
    """
    return ee.Image(f'ESA/WorldCover/v200/{year}').select('Map')


WORLD_COVER_CLASSES = {
    10: 'Tree cover',
    20: 'Shrubland',
    30: 'Grassland',
    40: 'Cropland',
    50: 'Built-up',
    60: 'Bare / sparse',
    70: 'Snow / ice',
    80: 'Permanent water',
    90: 'Herbaceous wetland',
    95: 'Moss / lichen',
    100: 'Mangroves',
}
