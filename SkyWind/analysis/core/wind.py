"""
wind.py
-------

This module contains wind-direction helpers and wind-rose logic.

It provides:
    • sector_from_degrees()  – classify wind direction into N/NE/E/SE/etc.
    • compute_wind_rose()    – build region-level wind rose from zones
    • deg_to_label()         – optional label formatter (0-360° → 'NNE')

This file has **no Django imports** and can be tested independently.
"""


# ---------------------------------------------------------
# WIND DIRECTION → SECTOR
# ---------------------------------------------------------

def sector_from_degrees(deg: float) -> str:
    """
    Convert wind direction in degrees (0–360) into a sector:
        N, NE, E, SE, S, SW, W, NW
    """

    if deg is None:
        return "N"

    # Normalize range
    deg = deg % 360

    if 337.5 <= deg or deg < 22.5:     return "N"
    if 22.5 <= deg < 67.5:             return "NE"
    if 67.5 <= deg < 112.5:            return "E"
    if 112.5 <= deg < 157.5:           return "SE"
    if 157.5 <= deg < 202.5:           return "S"
    if 202.5 <= deg < 247.5:           return "SW"
    if 247.5 <= deg < 292.5:           return "W"
    if 292.5 <= deg < 337.5:           return "NW"

    return "N"  # fallback (should never happen)


# ---------------------------------------------------------
# WIND ROSE (AVERAGE SPEED PER SECTOR)
# ---------------------------------------------------------

def compute_wind_rose(zones):
    """
    Build a wind rose for a list of Zone objects.

    zones: iterable of objects having:
        • avg_wind_speed (float)
        • wind_direction (float)

    Returns dict:
        {
            "N": 3.1,
            "NE": 4.2,
            "E": 1.8,
            ...
        }
    Where each value is the average speed in that sector.
    """

    bins = {
        "N": [], "NE": [], "E": [], "SE": [],
        "S": [], "SW": [], "W": [], "NW": []
    }

    # Bucket wind speeds
    for z in zones:
        sector = sector_from_degrees(z.wind_direction)
        bins[sector].append(z.avg_wind_speed)

    # Compute means
    rose = {}
    for sec, speeds in bins.items():
        if speeds:
            rose[sec] = round(sum(speeds) / len(speeds), 2)
        else:
            rose[sec] = 0.0

    return rose


# ---------------------------------------------------------
# DEGREE → 16-SECTOR COMPASS LABEL (optional)
# ---------------------------------------------------------

COMPASS_16 = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW",
]


def deg_to_label(deg: float) -> str:
    """
    Convert degree direction into 16-wind compass label:
        0° → N
        20° → NNE
        45° → NE
        ...
    Useful for readable display in the admin or frontend.
    """

    if deg is None:
        return "N"

    deg = deg % 360
    idx = int((deg + 11.25) // 22.5) % 16
    return COMPASS_16[idx]
