import requests
from django.conf import settings

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def get_grid_infrastructure(lat_min, lon_min, lat_max, lon_max):
    """
    Fetch high-voltage power lines and substations from OSM using Overpass.

    Args:
        lat_min, lon_min, lat_max, lon_max: region bounding box.

    Returns:
        dict with:
            - lines: GeoJSON FeatureCollection of transmission lines
            - substations: GeoJSON FeatureCollection of substations
    """

    # Build Overpass bounding box string
    bbox = f"{lat_min},{lon_min},{lat_max},{lon_max}"

    # --- QUERY 1: HIGH-VOLTAGE POWER LINES (major lines only) ---
    line_query = f"""
    [out:json][timeout:25];
    (
        way["power"="line"]({bbox});
    );
    out geom;
    """

    # --- QUERY 2: SUBSTATIONS (nodes + ways + relations) ---
    substation_query = f"""
    [out:json][timeout:25];
    (
        node["power"="substation"]({bbox});
        way["power"="substation"]({bbox});
        relation["power"="substation"]({bbox});
    );
    out geom;
    """

    def fetch(query):
        try:
            r = requests.post(OVERPASS_URL, data=query)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e), "elements": []}

    def to_geojson(osm):
        features = []

        for el in osm.get("elements", []):
            if "geometry" not in el:
                continue

            geom = el["geometry"]

            # Type: way → LineString (for lines)
            if el["type"] == "way":
                coords = [(p["lon"], p["lat"]) for p in geom]
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {"id": el["id"], "type": el["tags"].get("power", "")}
                })

            # Type: node → Point (for substations)
            elif el["type"] == "node":
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [el["lon"], el["lat"]]},
                    "properties": {"id": el["id"], "type": el["tags"].get("power", "")}
                })

            # Handle relation (substation area)
            elif el["type"] == "relation":
                # Some relations give a polygon outline
                if "members" in el:
                    rings = []
                    for mem in el["members"]:
                        if mem.get("geometry"):
                            ring = [(p["lon"], p["lat"]) for p in mem["geometry"]]
                            rings.append(ring)
                    if rings:
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": rings},
                            "properties": {"id": el["id"], "type": el["tags"].get("power", "")}
                        })

        return {"type": "FeatureCollection", "features": features}

    # Fetch OSM data
    raw_lines = fetch(line_query)
    raw_substations = fetch(substation_query)

    return {
        "lines": to_geojson(raw_lines),
        "substations": to_geojson(raw_substations),
    }
