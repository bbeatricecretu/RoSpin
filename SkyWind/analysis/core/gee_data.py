import ee

# Initialize Earth Engine once
ee.Initialize(project='rospin1')


# ---------------------------------------------------------
# TEMPERATURE
# ---------------------------------------------------------

def get_avg_temperature(lat: float, lon: float, year: int = 2023) -> float:
    """
    Return mean annual 2 m air temperature (°C) from ERA5-Land.
    T(K) -> T(°C) using: T = T(K) - 273.15.
    Averaged over all hourly values within 1 km radius.
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

def get_avg_wind_speeds(centers, year: int = 2023):
    """
    centers: list of (lat, lon) tuples — already rounded to ~5 decimals.
    Returns:
        dict[(lat, lon)] = {"speed": m/s, "direction": degrees (0–360)}
    """

    if not centers:
        return {}

    coll = (
        ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        .select(['u_component_of_wind_10m', 'v_component_of_wind_10m'])
        .filterDate(f'{year}-01-01', f'{year}-12-31')
    )

    mean = coll.mean()

    # Wind speed √(u² + v²)
    speed = mean.expression(
        'sqrt(u*u + v*v)',
        {
            'u': mean.select('u_component_of_wind_10m'),
            'v': mean.select('v_component_of_wind_10m'),
        }
    ).rename('wind_speed')

    # Wind direction atan2(u, v) -> degrees
    direction = mean.expression(
        '(180 / 3.14159265) * atan2(u, v)',
        {
            'u': mean.select('u_component_of_wind_10m'),
            'v': mean.select('v_component_of_wind_10m'),
        }
    ).rename('wind_dir')

    # Normalize to 0–360
    direction = direction.expression(
        '(dir + 360) % 360',
        {'dir': direction}
    )

    img = speed.addBands(direction)

    # Build FeatureCollection
    feats = [
        ee.Feature(
            ee.Geometry.Point([lon, lat]),
            {'lat_key': lat, 'lon_key': lon}
        )
        for lat, lon in centers
    ]

    fc = ee.FeatureCollection(feats)

    reduced = img.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=1000
    ).getInfo()

    result = {}
    for f in reduced['features']:
        p = f['properties']
        lat_key = p.get('lat_key')
        lon_key = p.get('lon_key')
        spd = p.get('wind_speed')
        direc = p.get('wind_dir')

        if lat_key is None or lon_key is None:
            continue

        result[(float(lat_key), float(lon_key))] = {
            'speed': float(spd) if spd is not None else 0.0,
            'direction': float(direc) if direc is not None else 0.0,
        }

    return result


# ---------------------------------------------------------
# DEM (Elevation, Slope, Tri)
# ---------------------------------------------------------

def get_dem_layers():
    """
    Returns: elevation (m), slope (°), terrain roughness (TRI)
    from Copernicus GLO-30 DEM.
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

def get_air_density_image(year: int = 2023):
    coll = (
        ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        .filterDate(f'{year}-01-01', f'{year}-12-31')
        .select(['surface_pressure', 'temperature_2m'])
    )

    mean = coll.mean()
    T = mean.select('temperature_2m')     # Kelvin
    P = mean.select('surface_pressure')   # Pascals
    R_d = 287.05

    rho = P.divide(T.multiply(R_d)).rename('air_density')
    return rho


# ---------------------------------------------------------
# WIND POWER DENSITY
# P = 0.5 * ρ * v³
# ---------------------------------------------------------

def get_wind_power_density_image(year: int = 2023):
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
        T = img.select('temperature_2m')   # K
        P = img.select('surface_pressure') # Pa
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
