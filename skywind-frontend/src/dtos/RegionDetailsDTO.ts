export interface LatLon { lat: number; lon: number; }

export interface RegionDetailsDTO {
  id: number;

  center: LatLon;
  A: LatLon;
  B: LatLon;
  C: LatLon;
  D: LatLon;

  avg_temperature: number;
  wind_rose: Record<string, number>;
  rating: number;
  avg_potential: number;
  infrastructure_rating: number;
  index_average: number;
  max_potential_zone: number | null;
}
