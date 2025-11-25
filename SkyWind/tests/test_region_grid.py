from analysis.core.entities import Point, Region

# === Define center of Cluj-Napoca ===
center_cluj = Point(46.7712, 23.6236)

# === Create Region and generate corners + grid ===
region = Region(center_cluj, None, None, None, None)
region.generate_corners()
region.generate_grid()

# === Display Region corners ===
print("=== REGION CORNERS (20 x 20 km square) ===")
print("A (upper-right):", region.A)
print("B (lower-right):", region.B)
print("C (lower-left):", region.C)
print("D (upper-left):", region.D)

# === Verify some sample zones ===
print("\n=== SAMPLE ZONES (each 2x2 km) ===")

# Top-left of matrix (row 0, col 0)
z_00 = region.zones[0][0]
print("Zone[1,1] (top-left cell):")
print("  A:", z_00.A)
print("  B:", z_00.B)
print("  C:", z_00.C)
print("  D:", z_00.D)

# Top-right of matrix (row 0, col 9)
z_09 = region.zones[0][9]
print("\nZone[1,10] (top-right cell):")
print("  A:", z_09.A)
print("  B:", z_09.B)
print("  C:", z_09.C)
print("  D:", z_09.D)

# Bottom-left (row 9, col 0)
z_90 = region.zones[9][0]
print("\nZone[10,1] (bottom-left cell):")
print("  A:", z_90.A)
print("  B:", z_90.B)
print("  C:", z_90.C)
print("  D:", z_90.D)

# Bottom-right (row 9, col 9)
z_99 = region.zones[9][9]
print("\nZone[10,10] (bottom-right cell):")
print("  A:", z_99.A)
print("  B:", z_99.B)
print("  C:", z_99.C)
print("  D:", z_99.D)
