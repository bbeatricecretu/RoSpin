"""
geometry.py
-----------

This module contains **pure geometry logic** for your wind-energy project.

It does NOT import Django, Earth Engine, or database models.
It only computes geographical coordinates:

    • compute_region_corners()
    • generate_zone_grid()

These functions are used by `generate_zones.py` to build RegionGrid and Zone
instances in the database.
"""

import math


# ---------------------------------------------------------
# REGION CORNERS
# ---------------------------------------------------------

def compute_region_corners(center_lat: float, center_lon: float, side_km: float):
    """
    Compute the 4 corners (A, B, C, D) of a square region centered at (lat, lon).

    Orientation:
        A = top-right
        B = bottom-right
        C = bottom-left
        D = top-left

    Return dict:
        {
            "A": (lat, lon),
            "B": (lat, lon),
            "C": (lat, lon),
            "D": (lat, lon),
        }
    """

    half = side_km / 2

    # Degree conversion:
    # 1 km ≈ 0.009° latitude
    deg_lat = 0.009
    deg_lon = 0.009 / math.cos(math.radians(center_lat))

    dlat = half * deg_lat
    dlon = half * deg_lon

    A = (center_lat + dlat, center_lon + dlon)  # top-right
    B = (center_lat - dlat, center_lon + dlon)  # bottom-right
    C = (center_lat - dlat, center_lon - dlon)  # bottom-left
    D = (center_lat + dlat, center_lon - dlon)  # top-left

    return {"A": A, "B": B, "C": C, "D": D}


# ---------------------------------------------------------
# ZONE GRID GENERATION
# ---------------------------------------------------------

def generate_zone_grid(A, B, C, D, n: int):
    """
    Generate an n×n grid of small zone polygons inside the region.

    Inputs:
        A, B, C, D = tuples (lat, lon) for region corners
        n = zones per edge

    Returns:
        A 2D list (n rows × n columns):
        [
            [ { "A": (...), "B": (...), "C": (...), "D": (...) }, ... ],
            ...
        ]

    Each zone is a dict with its 4 corners.
    """

    A_lat, A_lon = A
    B_lat, B_lon = B
    C_lat, C_lon = C
    D_lat, D_lon = D

    # Step size in degrees between adjacent zones
    step_lat = (B_lat - A_lat) / n     # top to bottom
    step_lon = (A_lon - D_lon) / n     # left to right

    grid = []

    for i in range(n):
        row = []
        for j in range(n):

            # Compute top-left corner (D_zone)
            top_left_lat = D_lat + i * step_lat
            top_left_lon = D_lon + j * step_lon

            # Define all 4 corners
            A_z = (top_left_lat,               top_left_lon + step_lon)  # top-right
            B_z = (top_left_lat + step_lat,    top_left_lon + step_lon)  # bottom-right
            C_z = (top_left_lat + step_lat,    top_left_lon)             # bottom-left
            D_z = (top_left_lat,               top_left_lon)             # top-left

            row.append({
                "A": A_z,
                "B": B_z,
                "C": C_z,
                "D": D_z,
            })

        grid.append(row)

    return grid
