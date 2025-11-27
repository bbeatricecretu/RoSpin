export interface LatLon { lat: number; lon: number; }

export interface ZoneDetailsDTO {
  id: number;
  zone_index: number;
  region_id: number;
  grid_id: number;

  A: LatLon;
  B: LatLon;
  C: LatLon;
  D: LatLon;

  avg_wind_speed: number;
  wind_direction: number;

  min_alt: number;
  max_alt: number;
  roughness: number;

  air_density: number;
  power_avg: number;

  land_type: string;
  potential: number;

  infrastructure: {
    index: number;
    km_jud: number;
    km_nat: number;
    km_euro: number;
    km_auto: number;
  };
}
