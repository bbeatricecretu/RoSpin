# analysis/services/relief_gee.py
import ee

# We assume ee.Initialize(...) is already called in your project
# (same way water_gee.py works)


def get_relief_points(
    lat_min: float, lon_min: float, lat_max: float, lon_max: float
) -> dict:
    """
    Sample elevation (DEM) points for the region bounding box.

    Returns a GeoJSON-style FeatureCollection with Point geometries
    and a 'DEM' property (elevation in meters).
    """

    # Rectangle: [west, south, east, north] = [lon_min, lat_min, lon_max, lat_max]
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

    # Copernicus DEM 30m
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation")

    # Sample points inside region (limit to keep response small)
    # scale ~ 90m is fine for visualization
    samples = dem.sample(
        region=region,
        scale=90,
        numPixels=2000,  # upper cap
        geometries=True,
    )

    # Earth Engine returns a FeatureCollection -> convert to dict
    fc_dict = samples.getInfo()
    # fc_dict already looks like a GeoJSON FeatureCollection

    return fc_dict
