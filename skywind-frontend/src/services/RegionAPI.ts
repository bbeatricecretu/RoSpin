import type { RegionComputeRequestDTO } from "../dtos/RegionComputeRequestDTO";
import type { RegionComputeResponseDTO } from "../dtos/RegionComputeResponseDTO";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";

const API_URL = "http://localhost:8000/api";

// ------------------------------------------------------------
// COMPUTE REGION  (POST /regions/compute/)
// ------------------------------------------------------------
export async function computeRegion(
  payload: RegionComputeRequestDTO
): Promise<RegionComputeResponseDTO> {

  const response = await fetch(`${API_URL}/regions/compute/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) throw new Error("Backend error during computeRegion");
  return response.json();
}

// ------------------------------------------------------------
// GET REGION DETAILS (GET /regions/:id/)
// ------------------------------------------------------------
export async function getRegionDetails(
  id: number
): Promise<RegionDetailsDTO> {
  const response = await fetch(`${API_URL}/regions/${id}/`);
  if (!response.ok) throw new Error("Region details fetch failed");
  return response.json();
}

// ------------------------------------------------------------
// GET REGION ZONES (GET /regions/:id/zones/)
// ------------------------------------------------------------
export async function getRegionZones(
  id: number
): Promise<ZoneDetailsDTO[]> {
  const response = await fetch(`${API_URL}/regions/${id}/zones/`);
  if (!response.ok) throw new Error("Zone list fetch failed");
  return response.json();
}

// ------------------------------------------------------------
// GET ONE ZONE DETAILS (GET /zones/:id/)
// ------------------------------------------------------------
export async function getZoneDetails(
  id: number
): Promise<ZoneDetailsDTO> {
  const response = await fetch(`${API_URL}/zones/${id}/`);
  if (!response.ok) throw new Error("Zone details fetch failed");
  return response.json();
}
