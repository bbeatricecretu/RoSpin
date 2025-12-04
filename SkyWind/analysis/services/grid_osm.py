import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ===============================================================
# BASIC BBOX CLIPPING (no shapely, fast, stable)
# ===============================================================


def clip_line_to_bbox(coords, lat_min, lon_min, lat_max, lon_max):
    """
    Clip a LineString to the region bounding box using Liang-Barsky.
    coords = list of (lon, lat) tuples
    Returns a list of clipped segments (each is a list of coords)
    """

    def inside(p):
        x, y = p
        return (lon_min <= x <= lon_max) and (lat_min <= y <= lat_max)

    def clip_segment(p1, p2):
        x0, y0 = p1
        x1, y1 = p2

        dx = x1 - x0
        dy = y1 - y0

        p = [-dx, dx, -dy, dy]
        q = [x0 - lon_min, lon_max - x0, y0 - lat_min, lat_max - y0]

        u1, u2 = 0.0, 1.0

        for pi, qi in zip(p, q):
            if pi == 0:
                if qi < 0:
                    return None
            else:
                t = qi / pi
                if pi < 0:
                    if t > u2:
                        return None
                    if t > u1:
                        u1 = t
                else:
                    if t < u1:
                        return None
                    if t < u2:
                        u2 = t

        nx0 = x0 + u1 * dx
        ny0 = y0 + u1 * dy
        nx1 = x0 + u2 * dx
        ny1 = y0 + u2 * dy

        return (nx0, ny0), (nx1, ny1)

    clipped = []
    for i in range(len(coords) - 1):
        seg = clip_segment(coords[i], coords[i + 1])
        if seg:
            clipped.append([seg[0], seg[1]])

    return clipped


# ===============================================================
# OSM → GEOJSON
# ===============================================================


def get_grid_infrastructure(lat_min, lon_min, lat_max, lon_max):
    bbox = f"{lat_min},{lon_min},{lat_max},{lon_max}"

    line_query = f"""
    [out:json][timeout:25];
    (
        way["power"="line"]({bbox});
    );
    out geom;
    """

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
        except Exception:
            return {"elements": []}

    raw_lines = fetch(line_query)
    raw_sub = fetch(substation_query)

    return {
        "lines": convert_lines(raw_lines, lat_min, lon_min, lat_max, lon_max),
        "substations": convert_substations(raw_sub, lat_min, lon_min, lat_max, lon_max),
    }


# ===============================================================
# LINE CONVERSION WITH CLIPPING
# ===============================================================


def convert_lines(osm, lat_min, lon_min, lat_max, lon_max):
    features = []

    for el in osm.get("elements", []):
        if el["type"] != "way" or "geometry" not in el:
            continue

        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]

        # Clip the line to region bounding box
        segments = clip_line_to_bbox(coords, lat_min, lon_min, lat_max, lon_max)
        if not segments:
            continue

        for seg in segments:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": seg},
                    "properties": {
                        "id": el["id"],
                        "power": el.get("tags", {}).get("power", ""),
                    },
                }
            )

    return {"type": "FeatureCollection", "features": features}


# ===============================================================
# SUBSTATIONS (POINTS ONLY)
# ===============================================================


def convert_substations(osm, lat_min, lon_min, lat_max, lon_max):
    features = []

    for el in osm.get("elements", []):
        if el["type"] != "node":
            continue

        x, y = el["lon"], el["lat"]

        if lon_min <= x <= lon_max and lat_min <= y <= lat_max:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [x, y]},
                    "properties": {
                        "id": el["id"],
                        "power": el.get("tags", {}).get("power", ""),
                    },
                }
            )

    return {"type": "FeatureCollection", "features": features}
