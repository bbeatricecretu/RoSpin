# from typing import List,Optional
# import math
#
# class Point:
#     def __init__(self, lat: float, lon: float):
#         self.lat = lat
#         self.lon = lon
#
#     def __repr__(self):
#         return f"Point({self.lat}, {self.lon})"
#
# class Infrastructure:
#     def __init__(self, index: int=0, km_jud: int = 0, km_nat: int = 0, km_euro: int = 0, km_auto: int = 0):
#         self.index = index
#         self.km_jud = km_jud
#         self.km_nat = km_nat
#         self.km_euro = km_euro
#         self.km_auto = km_auto
#
#     def __repr__(self):
#         return (f"Infrastructure(index={self.index}, km_jud={self.km_jud}, "
#                 f"km_nat={self.km_nat}, km_euro={self.km_euro}, km_auto={self.km_auto})")
#
#
# class EnergyStorage:
#     def __init__(self, name: str, coordinates: Point):
#         self.name = name
#         self.coordinates = coordinates
#
#     def __repr__(self):
#         return f"EnergyStorage(name={self.name}, coordinates={self.coordinates})"
#
# class Zone:
#     def __init__(self,
#                  A: Point,
#                  B: Point,
#                  C: Point,
#                  D: Point,
#                  min_alt: int = 0,
#                  max_alt: int = 0,
#                  roughness: int = 0,
#                  air_density: float = 0.0,
#                  avg_wind_speed: float = 0.0,
#                  power_avg: float = 0.0,
#                  land_type: str = "",
#                  potential: float = 0.0,
#
#                  infrastructure: Optional[Infrastructure] = None):
#         self.A = A
#         self.B = B
#         self.C = C
#         self.D = D
#         self.min_alt = min_alt
#         self.max_alt = max_alt
#         self.roughness = roughness
#         self.air_density = air_density
#         self.avg_wind_speed = avg_wind_speed
#         self.power_avg = power_avg
#         self.land_type = land_type
#         self.potential = potential
#         self.infrastructure = infrastructure or Infrastructure()
#
#     def __repr__(self):
#         return f"{self.A}, {self.B}, {self.C}"
#
# class Region:
#     def __init__(self,
#                  center: Point,
#                  A: Optional[Point]=None,
#                  B: Optional[Point]=None,
#                  C: Optional[Point]=None,
#                  D: Optional[Point]=None,
#                  avg_temperature: float = 0.0,
#                  wind_rose: Optional[List[float]] = None,#
#                  rating: int = 0,
#                  max_potential: Optional[Zone] = None,#
#                  avg_potential: float = 0.0,
#                  closest_storage: Optional[EnergyStorage] = None,
#                  infrastructure_rating: int = 0,
#                  zone_index: int = 0,
#                  index_average: float = 0.0):
#         self.center = center
#         self.A = A
#         self.B = B
#         self.C = C
#         self.D = D
#         self.avg_temperature = avg_temperature
#         self.wind_rose = wind_rose
#         self.rating = rating
#         self.max_potential = max_potential
#         self.avg_potential = avg_potential
#         self.closest_storage = closest_storage
#         self.infrastructure_rating = infrastructure_rating
#         self.index_average = index_average
#         self.zones: List[List[Zone]] = []
#         self.zone_index = zone_index
#
#     def __repr__(self):
#         return (f"{self.center}, {self.A}, {self.B}, {self.C}")
#
#     def generate_corners(self, side_km: float = 20.0):
#
#         half_km = side_km / 2
#
#         # Approximate degree conversions
#         deg_per_km_lat = 0.009  # 1 km ≈ 0.009° latitude
#         deg_per_km_lon = 0.009 / math.cos(math.radians(self.center.lat))
#
#         # Calculate deltas
#         delta_lon = half_km * deg_per_km_lon
#         delta_lat = half_km * deg_per_km_lat
#
#         # Clockwise from upper-right (A)
#         self.A = Point(self.center.lat + delta_lat, self.center.lon + delta_lon)  # upper-right
#         self.B = Point(self.center.lat - delta_lat, self.center.lon + delta_lon)  # lower-right
#         self.C = Point(self.center.lat - delta_lat, self.center.lon - delta_lon)  # lower-left
#         self.D = Point(self.center.lat + delta_lat, self.center.lon - delta_lon)  # upper-left
#
#         return self  # optional: allows chaining like region.generate_corners().generate_grid()
#
#     def generate_grid(self, n: int = 10):
#
#         if not all([self.A, self.B, self.C, self.D]):
#             raise ValueError("Corners not generated. Call generate_corners() first.")
#
#         self.zones = []
#
#         # Step size between adjacent zones in degrees
#         step_lat = (self.B.lat - self.A.lat) / n     # north→south NEGATIVE
#         step_lon = (self.A.lon - self.D.lon) / n       # west→east POSITIVE
#
#         for i in range(n):
#             row = []
#             for j in range(n):
#                 # Compute the top-left corner (D_zone) of this cell
#                 top_left_lat = self.D.lat + i * step_lat
#                 top_left_lon = self.D.lon + j * step_lon
#
#                 # Now define all 4 corners clockwise starting from top-right (A)
#                 A_zone = Point(top_left_lat, top_left_lon + step_lon)       # top-right
#                 B_zone = Point(top_left_lat + step_lat, top_left_lon + step_lon)  # bottom-right
#                 C_zone = Point(top_left_lat + step_lat, top_left_lon)       # bottom-left
#                 D_zone = Point(top_left_lat, top_left_lon)                  # top-left
#
#                 zone = Zone(A_zone, B_zone, C_zone, D_zone)
#                 row.append(zone)
#
#             self.zones.append(row)
#
# def region_to_geojson(region: Region) -> dict:
#     features = []
#
#     #The main polygon
#     features.append({
#         "type": "Feature",
#         "properties":{"name": "Region Polygon"},
#         "geometry": {
#             "type": "Polygon",
#             "coordinates": [[
#                 [region.A.lon, region.A.lat],
#                 [region.B.lon, region.B.lat],
#                 [region.C.lon, region.C.lat],
#                 [region.D.lon, region.D.lat],
#                 [region.A.lon, region.A.lat],
#             ]]
#         }
#
#     })
#
#     #The center point
#
#     features.append({
#         "type": "Feature",
#         "properties": {"name": "center point"},
#         "geometry": {
#             "type": "Point",
#             "coordinates": [region.center.lon, region.center.lat]
#         }
#
#     })
#
#     for label, p in zip(["A", "B", "C", "D"], [region.A, region.B, region.C, region.D]):
#         features.append({
#             "type": "Feature",
#             "properties": {"name": f"Point {label}"},
#             "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]}
#         })
#
#     for i, row in enumerate(region.zones, start = 1):
#         for j, z in enumerate(row, start = 1):
#             features.append({
#                 "type": "Feature",
#                 "properties": {"name": f"Zone[{i},{j}]"},
#                 "geometry": {
#                     "type": "Polygon",
#                     "coordinates": [[
#                         [z.A.lon, z.A.lat],
#                         [z.B.lon, z.B.lat],
#                         [z.C.lon, z.C.lat],
#                         [z.D.lon, z.D.lat],
#                         [z.A.lon, z.A.lat],
#                     ]]
#                 }
#             })
#     return {"type": "FeatureCollection", "features": features}
