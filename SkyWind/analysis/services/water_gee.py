import ee

def get_water_polygons(lat_min, lon_min, lat_max, lon_max):
    # Same bbox logic as before
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

    # OSM-based global water mask (90 m)
    coll = ee.ImageCollection("projects/sat-io/open-datasets/OSM_waterLayer")
    osm_water = coll.mosaic()  # merge all tiles

    # Keep all inland water classes: 2–5
    water_mask = osm_water.gte(2).And(osm_water.lte(5))

    # Optional: thicken thin streams a bit so they don't break
    water_mask = water_mask.focal_max(radius=1, units="pixels")

    # Build image for reduceToVectors
    mask_band = water_mask.rename("water")
    const_band = ee.Image.constant(1).rename("constant")
    img = mask_band.addBands(const_band)

    vectors = img.reduceToVectors(
        geometry=region,
        scale=90,              # native resolution of OSM_waterLayer
        geometryType="polygon",
        labelProperty="water",
        reducer=ee.Reducer.sum(),
        maxPixels=1e9,
    )

    return vectors.getInfo()


