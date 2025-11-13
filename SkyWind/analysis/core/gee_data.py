import ee

ee.Initialize(project = 'rospin1')

def get_avg_temperature(lat, lon, year=2023): #initialize a function with lat lon and year parameters
    """Return mean annual temperature in degrees Celsius from ERA5-Land"""
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

# def get_avg_wind_speed(lat, lon, year=2023):
#     """Return mean annual wind speed in m/s^2 from ERA5-Land"""
#
#     coll = (ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
#         .select(['u_component_of_wind_10m', 'v_component_of_wind_10m'])
#         # two bands are selected the east and west components of the wind
#
#         .filterDate(f'{year}-01-01', f'{year}-12-31')) #filter
#     mean = coll.mean() # computes the mean for each pixel across the entire year
#
#     speed = mean.expression('sqrt(u**2 + v**2)',
#
#     # speed variable will take the value of a mathematical formula that
#     # gives the true scalar wind speed using the 2 components
#
#     {
#         'u' : mean.select('u_component_of_wind_10m'),
#         'v' : mean.select('v_component_of_wind_10m'),
#     }).rename('wind_speed')
#
#     point = ee.Geometry.Point([lon, lat]) # creates the geographical point for the computations
#
#     val = speed.reduceRegion(ee.Reducer.mean(), point, 1000).get('wind_speed')
#     # takes all pixels in a 1km radius around the point and reduce them to the same value
#
#     return round (float(val.getInfo()), 2)

def get_avg_wind_speeds(points, year=2023):
    """Return a dict mapping (lat, lon) → mean annual wind speed (m/s) for many points at once."""
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
    """Return elevation (m), slope (deg), and TRI-like ruggedness (stddev of 3x3 neighborhood)."""
    # Mosaic DEM tiles and select the elevation band
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30").mosaic().select("DEM").rename("elevation")

    # Slope in degrees
    slope = ee.Terrain.slope(dem).rename("slope")

    # TRI-like ruggedness: std dev of elevation in a 3x3 pixel window
    kernel = ee.Kernel.square(radius=1, units='pixels')  # 3x3 neighborhood
    tri = dem.reduceNeighborhood(
        reducer=ee.Reducer.stdDev(),
        kernel=kernel
    ).rename("tri")

    return dem.addBands([slope, tri])
