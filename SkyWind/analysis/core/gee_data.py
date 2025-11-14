import ee

ee.Initialize(project = 'rospin1')

def get_avg_temperature(lat, lon, year=2023): #initialize a function with lat lon and year parameters
    """ Returns mean annual 2 m air temperature (°C) for a given location using ERA5-Land data.
    Temperature is computed as T(°C) = T(K) − 273.15, averaged over all hourly records
    of the selected year within a 1 km radius around the point."""
    coll = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY') \
        .select('temperature_2m') \
        .filterDate(f'{year}-01-01', f'{year}-12-31')

    #ECMWF → dataset provider = European Centre for Medium - Range Weather Forecasts
    #ERA5_LAND → dataset version = ERA5-Land Reanalysis,
    #HOURLY → temporal resolution = data available hourly for each day.
    #temperature_2m -> air temperature 2 m above surface, in Kelvin)

    img = coll.mean() # mean = methods that computes per pixel mean across an entire collection
    #coll -> is an ee.ImageCollection that stack hundreds on images from a year and calculates their average

    point = ee.Geometry.Point([lon, lat]) # creates a geometric point

    val = img.reduceRegion(ee.Reducer.mean(), point, 1000).get('temperature_2m')
    #basically we take one point ad apply the mean temperature from that point to the entire 1km radios accros that point

    return round(float(val.getInfo()) - 273.15, 2) # return the rounded temperature in Celsius


def get_avg_wind_speeds(points, year=2023):
    """ Returns mean annual 10 m wind speed (m/s) for multiple points using ERA5-Land data.
    Wind speed is computed as v = √(u² + v²), where u and v are the east–west and
    north–south wind components averaged over the selected year."""
    coll = (ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        .select(['u_component_of_wind_10m', 'v_component_of_wind_10m'])
        .filterDate(f'{year}-01-01', f'{year}-12-31'))

    mean = coll.mean()
    speed = mean.expression(
        'sqrt(u**2 + v**2)',
        {
            'u': mean.select('u_component_of_wind_10m'),
            'v': mean.select('v_component_of_wind_10m'),
        }
    ).rename('wind_speed')

    # Make a FeatureCollection of all points
    features = [ee.Feature(ee.Geometry.Point([lon, lat])) for lat, lon in points]
    fc = ee.FeatureCollection(features)

    # Compute mean wind speed for all points at once
    results = speed.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=1000
    ).getInfo()

    # Convert results back to Python dict
    speeds = {}
    for feature, (lat, lon) in zip(results['features'], points):
        val = feature['properties'].get('mean')
        speeds[(lat, lon)] = round(float(val), 2) if val is not None else None

    return speeds

def get_dem_layers():
    """Returns elevation (m), slope (°), and terrain roughness (TRI) from Copernicus GLO-30.
    Roughness is computed as TRI = σ(Zₙ), the standard deviation of elevation values
    within an 11×11 pixel (~330 m) neighborhood."""
    # Mosaic DEM tiles and select the elevation band
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30").mosaic().select("DEM").rename("elevation")

    # Slope in degrees
    slope = ee.Terrain.slope(dem).rename("slope")

    # TRI-like ruggedness: std dev of elevation in a 3x3 pixel window
    kernel = ee.Kernel.square(radius=5, units='pixels')  # 11x11 (~330 m)
    tri = dem.reduceNeighborhood(
        reducer=ee.Reducer.stdDev(),
        kernel=kernel
    ).rename("tri")

    return dem.addBands([slope, tri])

def get_air_density_image(year=2023):
    """
    Returns an image of air density (kg/m³) computed from ERA5-Land mean surface
    pressure (p) and 2 m temperature (T) using ρ = p / (R_d * T), where R_d = 287.05 J/(kg·K).
    """
    coll = (ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
            .filterDate(f'{year}-01-01', f'{year}-12-31')
            .select(['surface_pressure', 'temperature_2m']))
    
    mean = coll.mean()
    T = mean.select('temperature_2m')         # Kelvin
    P = mean.select('surface_pressure')       # Pascals
    R_d = 287.05                              # gas constant for dry air
    
    rho = P.divide(T.multiply(R_d)).rename('air_density')  # ρ = p / (R_d * T)
    return rho


def get_wind_power_density_image(year=2023):
    """
    Returns an image of mean wind power density (W/m²) computed as:
        P_d = 0.5 * ρ * v³
    where:
        ρ = p / (R_d * T)  (air density)
        v = √(u² + v²)     (wind speed magnitude)
    """
    coll = (ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
            .filterDate(f'{year}-01-01', f'{year}-12-31')
            .select([
                'u_component_of_wind_10m',
                'v_component_of_wind_10m',
                'surface_pressure',
                'temperature_2m'
            ]))

    def per_hour(img):
        u = img.select('u_component_of_wind_10m')
        v = img.select('v_component_of_wind_10m')
        T = img.select('temperature_2m')         # K
        P = img.select('surface_pressure')       # Pa
        R_d = 287.05
        speed = u.pow(2).add(v.pow(2)).sqrt()
        rho = P.divide(T.multiply(R_d))          # ρ = p / (R_d * T)
        pd = rho.multiply(speed.pow(3)).multiply(0.5).rename('power_density')
        return pd

    pd_coll = coll.map(per_hour)
    return pd_coll.mean().rename('power_density')


def get_landcover_image(year=2021):
    """
    Return ESA WorldCover v200 dominant land cover band 'Map' (10 m).
    Valid years in v200: 2020 or 2021. We default to 2021.
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
    100: 'Mangroves'
}