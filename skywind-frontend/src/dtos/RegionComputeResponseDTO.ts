export interface RegionComputeResponseDTO {
  region_id: number;
  center: { lat: number; lon: number };
  corners: {
    A: { lat: number; lon: number } | null;
    B: { lat: number; lon: number } | null;
    C: { lat: number; lon: number } | null;
    D: { lat: number; lon: number } | null;
  };
  zones: {
    id: number;
    index: number;
    A: { lat: number; lon: number };
    B: { lat: number; lon: number };
    C: { lat: number; lon: number };
    D: { lat: number; lon: number };
  }[];
}
