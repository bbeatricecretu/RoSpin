export interface ZoneDTO {
  id: number;
  zone_index: number;

  A: { lat: number; lon: number };
  B: { lat: number; lon: number };
  C: { lat: number; lon: number };
  D: { lat: number; lon: number };

  avg_wind_speed: number;
  min_alt: number;
  max_alt: number;
  roughness: number;
  air_density: number;
  power_avg: number;
  land_type: string;
  potential: number;
  infrastructure_id: number | null;
}
