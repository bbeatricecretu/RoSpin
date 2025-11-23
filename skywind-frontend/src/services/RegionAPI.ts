//Frontend's API layer

import type { RegionComputeRequestDTO } from "../dtos/RegionComputeRequestDTO";
import type { RegionComputeResponseDTO } from "../dtos/RegionComputeResponseDTO";
import type{ ZoneDTO } from "../dtos/ZoneDTO";

const API_URL = "http://localhost:8000/api";
//Constant pointing to your Django backend.
//All API calls reuse this

//COMPUTE REGION
export async function computeRegion(payload: RegionComputeRequestDTO): Promise<RegionComputeResponseDTO> {

  const response = await fetch(`${API_URL}/regions/compute/`, {
    method: "POST", //sends data to compute a region.
    headers: { "Content-Type": "application/json" }, //Tells Django that you are sending JSON.
    body: JSON.stringify(payload), //Converts your TypeScript object into JSON string.
  });

  if (!response.ok) { //response.ok is false if HTTP status is 400–599.
    throw new Error("Backend error during computeRegion");
  }

  return response.json();
}

//GET_REGION_DETAILS
export async function getRegionDetails(id: number): Promise<RegionComputeResponseDTO> {
  const response = await fetch(`${API_URL}/regions/${id}/`);
  return response.json();
}

//GET_ZONE_DETAILS
export async function getRegionZones(id: number): Promise<ZoneDTO[]> {
  const response = await fetch(`${API_URL}/regions/${id}/zones/`);
  return response.json();
}
