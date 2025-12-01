import { useState } from "react";
import "./GeneratePage.css";
import { computeRegion } from "../services/RegionAPI";
import { useNavigate } from "react-router-dom";

import logo from "../assets/logo.png";
import windBg from "../assets/wind-bg2.png";

export default function GeneratePage() {
  const navigate = useNavigate();

  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [side, setSide] = useState("");
  const [zones, setZones] = useState("");

  const [helpOpen, setHelpOpen] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const payload = {
      lat: parseFloat(lat),
      lon: parseFloat(lon),
      side_km: parseFloat(side),
      zones_per_edge: parseInt(zones),
    };

    const result = await computeRegion(payload);
    navigate("/region", { state: result });
  }

  return (
    <div className="generate-container">
      
      {/* HERO */}
      <div className="generate-hero">
        <img src={windBg} className="generate-hero-bg" />
        <div className="generate-hero-overlay" />

        <div className="generate-hero-content">
          <img src={logo} alt="SkyWind" className="generate-hero-logo" />
          <h1 className="generate-title">Generate a Region</h1>
          <p className="generate-subtitle">
            Enter parameters to compute a new geospatial region.
          </p>
        </div>
      </div>

      {/* HELP BUTTON */}
      <button className="help-toggle-btn" onClick={() => setHelpOpen(true)}>
        ❔ Help
      </button>
<div className={`help-panel ${helpOpen ? "open" : ""}`}>
  <div className="help-header">
    <h3>How to Use</h3>
    <button className="help-close" onClick={() => setHelpOpen(false)}>×</button>
  </div>

  <p>Generate a custom geospatial region by filling the fields below.</p>

  <ul>
    <li>
      <strong>Latitude & Longitude: </strong>  
      The geographic point at the <em>center</em> of your analysis area.  
      Example: <strong>46.77, 23.59</strong> (Cluj-Napoca).
    </li>

    <li>
      <strong>Side Length (km): </strong>  
      The total width of the square region.  
      Larger values = bigger coverage area.
    </li>

    <li>
      <strong>Zones per Edge: </strong>  
      The number of grid divisions along each edge.  
      Example: <strong>5</strong> → creates a <strong>5×5 grid</strong> (25 zones).
    </li>

    <li>
      <strong>Use My Location: </strong>  
      Automatically fills in your device’s current coordinates.
    </li>
  </ul>

  <h4 style={{ marginTop: "14px", color: "var(--primary)" }}>Recommended Settings</h4>
  <ul>
    <li><strong>2–5 km</strong> side length for balanced detail & performance.</li>
    <li><strong>6–10 zones</strong> per edge for clean visualization.</li>
    <li>Use a larger grid (8–12) only for high-precision analysis.</li>
  </ul>

  <p style={{ marginTop: "12px" }}>
    The results will appear on an interactive map where each zone includes  
    wind metrics, suitability score, and turbine power estimation.
  </p>
</div>

      {/* MAIN CONTENT */}
      <div className="generate-main">

        <form className="wizard-card" onSubmit={handleSubmit}>
          <h2 className="wizard-title">Region Parameters</h2>

          {/* Step 1 */}
          <div className="wizard-section">
            <h3 className="wizard-step">📍 Step 1 — Select Location</h3>

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

            <button
              className="small-btn"
              type="button"
              onClick={() => {
                navigator.geolocation.getCurrentPosition((pos) => {
                  setLat(String(pos.coords.latitude));
                  setLon(String(pos.coords.longitude));
                });
              }}
            >
              Use My Location
            </button>
          </div>

          {/* Step 2 */}
          <div className="wizard-section">
            <h3 className="wizard-step">📦 Step 2 — Configure Grid</h3>

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
          </div>

          <button className="compute-btn" type="submit">
            Compute Region
          </button>
        </form>

        {/* WHAT YOU GET */}
        <div className="section-block">
          <h2 className="section-title">🎯 What You’ll Get</h2>
          <ul className="bullet-list">
            <li>Interactive map of your selected region</li>
            <li>Wind speed, air density & turbine power per zone</li>
            <li>Environmental suitability scoring (0–100)</li>
            <li>Coordinates & boundaries for each grid cell</li>
          </ul>
        </div>

      </div>
    </div>
  );
}