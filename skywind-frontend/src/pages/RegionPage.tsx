import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import logo from "../assets/logo.svg";
import RegionMap from "../components/RegionMap";
import type { RegionComputeResponseDTO } from "../dtos/RegionComputeResponseDTO";

export default function RegionPage() {
  const { state } = useLocation();
  const navigate = useNavigate();

  const region = state as RegionComputeResponseDTO | null;
  const [selectedZone, setSelectedZone] = useState<any>(null);

  if (!region) {
    return (
      <div className="region-page">
        <div className="details-card" style={{ maxWidth: "600px", margin: "auto" }}>
          <h2>No Region Data</h2>
          <p style={{ marginBottom: "20px", color: "var(--text-secondary)" }}>
            Please compute a region first to view the map and details.
          </p>
          <button
            className="submit-btn"
            onClick={() => navigate("/")}
            style={{ width: "auto", padding: "12px 24px" }}
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  function formatCoordinate(value: number): string {
    return value.toFixed(6);
  }

  return (
    <div className="region-page fade-in">
      {/* LEFT SIDE - MAP */}
      <div className="region-left">
        <div className="region-header">
          <img src={logo} alt="SkyWind Logo" />
          <div>
            <h2>Region Map</h2>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", margin: 0 }}>
              {region.zones.length} zones • Click a zone to view details
            </p>
          </div>
        </div>

        <div className="region-map-container">
          <RegionMap region={region} onZoneSelect={setSelectedZone} />
        </div>
      </div>

      {/* RIGHT SIDE - DETAILS */}
      <div className="region-right">
        {/* REGION INFO */}
        <div className="details-card">
          <h2>Region Details</h2>
          <div className="region-info">
            <div className="region-group">
              <h4>📍 Center Coordinates</h4>
              <div className="region-line">
                <strong>Latitude:</strong>
                <span>{formatCoordinate(region.center.lat)}</span>
              </div>
              <div className="region-line">
                <strong>Longitude:</strong>
                <span>{formatCoordinate(region.center.lon)}</span>
              </div>
            </div>

            <div className="region-group">
              <h4>🔲 Boundary Corners</h4>
              <div className="region-line">
                <strong>North-East (A):</strong>
                <span>
                  {formatCoordinate(region.corners.A.lat)},{" "}
                  {formatCoordinate(region.corners.A.lon)}
                </span>
              </div>
              <div className="region-line">
                <strong>South-East (B):</strong>
                <span>
                  {formatCoordinate(region.corners.B.lat)},{" "}
                  {formatCoordinate(region.corners.B.lon)}
                </span>
              </div>
              <div className="region-line">
                <strong>South-West (C):</strong>
                <span>
                  {formatCoordinate(region.corners.C.lat)},{" "}
                  {formatCoordinate(region.corners.C.lon)}
                </span>
              </div>
              <div className="region-line">
                <strong>North-West (D):</strong>
                <span>
                  {formatCoordinate(region.corners.D.lat)},{" "}
                  {formatCoordinate(region.corners.D.lon)}
                </span>
              </div>
            </div>

            <div className="region-group">
              <h4>📊 Statistics</h4>
              <div className="region-line">
                <strong>Total Zones:</strong>
                <span>{region.zones.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* ZONE INFO */}
        <div className="details-card">
          <h2>Zone Details</h2>

          {!selectedZone ? (
            <div className="zone-placeholder">
              <p style={{ fontSize: "48px", marginBottom: "16px" }}>🗺️</p>
              <p>Click on a zone on the map to view its details</p>
              <p style={{ fontSize: "14px", marginTop: "8px" }}>
                Zones are color-coded by potential
              </p>
            </div>
          ) : (
            <div className="zone-info">
              <div className="zone-title">Zone {selectedZone.index}</div>

              <div className="zone-section">
                <h4>📍 Coordinates</h4>
                <div className="zone-metric">
                  <span className="zone-metric-label">North-East (A):</span>
                  <span className="zone-metric-value">
                    {formatCoordinate(selectedZone.A.lat)},{" "}
                    {formatCoordinate(selectedZone.A.lon)}
                  </span>
                </div>
                <div className="zone-metric">
                  <span className="zone-metric-label">South-East (B):</span>
                  <span className="zone-metric-value">
                    {formatCoordinate(selectedZone.B.lat)},{" "}
                    {formatCoordinate(selectedZone.B.lon)}
                  </span>
                </div>
                <div className="zone-metric">
                  <span className="zone-metric-label">South-West (C):</span>
                  <span className="zone-metric-value">
                    {formatCoordinate(selectedZone.C.lat)},{" "}
                    {formatCoordinate(selectedZone.C.lon)}
                  </span>
                </div>
                <div className="zone-metric">
                  <span className="zone-metric-label">North-West (D):</span>
                  <span className="zone-metric-value">
                    {formatCoordinate(selectedZone.D.lat)},{" "}
                    {formatCoordinate(selectedZone.D.lon)}
                  </span>
                </div>
              </div>

              {selectedZone.potential !== undefined && (
                <div className="zone-section">
                  <h4>⚡ Energy Potential</h4>
                  <div className="zone-metric">
                    <span className="zone-metric-label">Potential:</span>
                    <span className="zone-metric-value highlight">
                      {selectedZone.potential.toFixed(2)}
                    </span>
                  </div>
                </div>
              )}

              {selectedZone.avg_wind_speed !== undefined && (
                <div className="zone-section">
                  <h4>💨 Wind Data</h4>
                  <div className="zone-metric">
                    <span className="zone-metric-label">Avg Wind Speed:</span>
                    <span className="zone-metric-value">
                      {selectedZone.avg_wind_speed.toFixed(2)} m/s
                    </span>
                  </div>
                </div>
              )}

              <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid var(--border-color)" }}>
                <button
                  className="submit-btn"
                  onClick={() => setSelectedZone(null)}
                  style={{ width: "100%", padding: "10px" }}
                >
                  Clear Selection
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
