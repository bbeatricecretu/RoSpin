import { useState } from "react";
import { computeRegion } from "../services/RegionAPI";
import { useNavigate } from "react-router-dom";
import type { RegionComputeResponseDTO } from "../dtos/RegionComputeResponseDTO.ts";

import logo from "../assets/logo.svg";
import wallpaper from "../assets/wallpaper.png";

export default function GeneratePage() {
  const navigate = useNavigate();

  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [side, setSide] = useState("");
  const [zones, setZones] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const payload = {
      lat: parseFloat(lat),
      lon: parseFloat(lon),
      side_km: parseFloat(side),
      zones_per_edge: parseInt(zones),
    };

    const result: RegionComputeResponseDTO = await computeRegion(payload);

    navigate("/region", { state: result });
  }

  return (
    <div>
      {/* HERO SECTION */}
      <div
        className="hero"
        style={{ backgroundImage: `url(${wallpaper})` }}
      >
        <div className="hero-overlay"></div>

        <div className="hero-content">
          <img src={logo} alt="SkyWind" style={{ width: "130px" }} />
          <h1 className="hero-title">Generate a Region</h1>
          <p className="hero-subtitle">
            Enter coordinates to compute a new region.
          </p>
        </div>
      </div>

      {/* FORM SECTION */}
      <div className="form-section">
        <h2 className="form-title">Region Parameters</h2>

        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "15px" }}
        >
          <input
            className="input-field"
            type="number"
            placeholder="Latitude"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
          />

          <input
            className="input-field"
            type="number"
            placeholder="Longitude"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
          />

          <input
            className="input-field"
            type="number"
            placeholder="Side Length (km)"
            value={side}
            onChange={(e) => setSide(e.target.value)}
          />

          <input
            className="input-field"
            type="number"
            placeholder="Zones per Edge"
            value={zones}
            onChange={(e) => setZones(e.target.value)}
          />

          <button className="submit-btn" type="submit">
            Compute
          </button>
        </form>
      </div>
    </div>
  );
}