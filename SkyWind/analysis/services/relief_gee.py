# analysis/services/relief_gee.py
import ee

# We assume ee.Initialize(...) is already called in your project
# (same way water_gee.py works)


def get_relief_tile_url(region):
    """
    Returns a tile URL for a continuous relief/topography layer.
    Uses Google Earth Engine to create a colorized elevation map with high contrast.
    
    Color scheme (low to high elevation) - High contrast, brownish peaks:
    - Bright green (#00ff00): Lowlands / plains - maximum saturation
    - Pure yellow (#ffff00): Low elevations - high contrast from green
    - Bright orange (#ff8800): Hills - strong contrast
    - Deep orange (#ff6600): Moderate elevation - vibrant
    - Chocolate (#d2691e): Mountains - brown-orange transition
    - Sienna (#a0522d): High mountains - rich brown
    - Saddle brown (#8b4513): Peaks - distinct brown
    - Very dark brown (#5c4033): Very high peaks - maximum brown contrast
    """
    # Load DEM
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation")

    # Get actual min/max elevation in the region for better color distribution
    # This ensures we use the full color range available in the region
    region_bounds = ee.Geometry.Polygon([
        [region.A.lon, region.A.lat],
        [region.B.lon, region.B.lat],
        [region.C.lon, region.C.lat],
        [region.D.lon, region.D.lat],
        [region.A.lon, region.A.lat],
    ])
    
    # Calculate min/max elevation in the region
    elevation_stats = dem.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=region_bounds,
        scale=100,  # Use 100m scale for faster computation
        maxPixels=1e9
    )
    
    # Get the computed min/max values
    stats_dict = elevation_stats.getInfo()
    elev_min = stats_dict.get('elevation_min', 0)
    elev_max = stats_dict.get('elevation_max', 2000)
    
    # Ensure we have a reasonable range
    if elev_max <= elev_min:
        elev_min = 0
        elev_max = 2000
    else:
        # Add some padding to ensure we see color variation
        # If the range is too small, expand it
        elev_range = elev_max - elev_min
        if elev_range < 50:  # If range is less than 50m, expand it
            padding = 25
            elev_min = max(0, elev_min - padding)
            elev_max = elev_max + padding
    
    # Define diverse, high-contrast color palette for elevation
    # Format: hex colors without #
    # Using highly saturated colors with maximum contrast, transitioning to brown tones at higher elevations
    palette = [
        "00ff00",  # 0m: Bright green (lowlands/plains) - maximum saturation
        "ffff00",  # Low: Pure yellow (low elevations) - high contrast from green
        "ff8800",  # Low-medium: Bright orange (hills) - strong contrast
        "ff6600",  # Medium: Deep orange (moderate elevation) - vibrant
        "d2691e",  # Medium-high: Chocolate (mountains) - brown-orange transition
        "a0522d",  # High: Sienna (high mountains) - rich brown
        "8b4513",  # Very high: Saddle brown (peaks) - distinct brown
        "5c4033",  # Highest: Very dark brown (very high peaks) - maximum brown contrast
    ]

    # Visualize with elevation-based coloring using region-specific min/max
    # This creates a smooth gradient that uses the full color range
    styled = dem.visualize(
        min=elev_min,
        max=elev_max,
        palette=palette,
    )

    # Get region polygon
    coords = [
        [region.A.lon, region.A.lat],
        [region.B.lon, region.B.lat],
        [region.C.lon, region.C.lat],
        [region.D.lon, region.D.lat],
        [region.A.lon, region.A.lat],
    ]
    geom = ee.Geometry.Polygon([coords])

    # Clip the styled image to the region
    final = styled.clip(geom)

    # Get tile URL
    map_id = ee.data.getMapId({'image': final})
    tile_url = map_id['tile_fetcher'].url_format

    return tile_url


def get_elevation_at_point(lat: float, lon: float) -> float:
    """
    Get elevation in meters at a specific point using DEM data.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
    
    Returns:
        float: Elevation in meters
    """
    # Load DEM
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation")
    
    # Create point geometry
    point = ee.Geometry.Point([lon, lat])
    
    # Sample elevation at the point
    elevation = dem.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=30,  # SRTM resolution is ~30m
        maxPixels=1e9
    ).get('elevation')
    
    # Get the elevation value
    elev_value = elevation.getInfo()
    
    # Handle missing data
    if elev_value is None:
        return 0.0
    
    return round(float(elev_value), 2)


def get_relief_points(
    lat_min: float, lon_min: float, lat_max: float, lon_max: float
) -> dict:
    """
    Sample elevation (DEM) points for the region bounding box.
    DEPRECATED: Use get_relief_tile_url for tile layer instead.

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
