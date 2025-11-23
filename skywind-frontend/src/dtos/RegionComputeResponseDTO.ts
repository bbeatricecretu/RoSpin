export interface ZoneComputeDTO {
  index: number;
  A: { lat: number; lon: number };
  B: { lat: number; lon: number };
  C: { lat: number; lon: number };
  D: { lat: number; lon: number };
}

export interface RegionComputeResponseDTO {
  center: { lat: number; lon: number };
  corners: {
    A: { lat: number; lon: number };
    B: { lat: number; lon: number };
    C: { lat: number; lon: number };
    D: { lat: number; lon: number };
  };
  zones: ZoneComputeDTO[];
}
