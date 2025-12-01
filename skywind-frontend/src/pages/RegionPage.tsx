import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import logo from "../assets/logo.svg";

import RegionMap from "../components/RegionMap";
import RegionDetails from "../components/RegionDetails";
import ZoneDetails from "../components/ZoneDetails";

import {
  getRegionDetails,
  getRegionZones,
  getZoneDetails,
  getRegionZonePowers,
} from "../services/RegionAPI.ts";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";

type ZonePowerRow = {
  id: number;
  zone_index: number;
  A: { lat: number; lon: number };
  B: { lat: number; lon: number };
  C: { lat: number; lon: number };
  D: { lat: number; lon: number };
  power_kw: number;
  avg_wind_speed: number;
  air_density: number;
};

export default function RegionPage() {
  const { state } = useLocation();
  const navigate = useNavigate();

  const regionId = state?.region_id ?? null;

  const [regionDetails, setRegionDetails] = useState<RegionDetailsDTO | null>(null);
  const [zones, setZones] = useState<ZoneDetailsDTO[]>([]);
  const [selectedZone, setSelectedZone] = useState<ZoneDetailsDTO | null>(null);

  const [selectedTurbineId, setSelectedTurbineId] = useState<number>(1);
  const [zonePowers, setZonePowers] = useState<ZonePowerRow[]>([]);

  useEffect(() => {
    if (!regionId) return;

    async function load() {
      const r = await getRegionDetails(regionId);
      const z = await getRegionZones(regionId);

      setRegionDetails(r);
      setZones(z);
    }

    load();
  }, [regionId]);

  useEffect(() => {
    if (!regionId || !selectedTurbineId) return;

    async function loadPowers() {
      try {
        const rows = await getRegionZonePowers(regionId, selectedTurbineId);
        setZonePowers(rows);
      } catch (e) {
        console.error("Failed to load zone powers", e);
        setZonePowers([]);
      }
    }

    loadPowers();
  }, [regionId, selectedTurbineId]);

  async function handleZoneClick(zoneId: number) {
    const fullZone = await getZoneDetails(zoneId);
    setSelectedZone(fullZone);
  }

  if (!regionId) {
    return (
      <div className="region-page">
        <div className="details-card" style={{ maxWidth: "600px", margin: "auto" }}>
          <h2>No Region Data</h2>
          <p style={{ marginBottom: "20px", color: "var(--text-secondary)" }}>
            Please compute a region first to view the map and details.
          </p>
          <button
            className="submit-btn"
            onClick={() => navigate("/generate")}
            style={{ width: "auto", padding: "12px 24px" }}
          >
            Go to Generate Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="region-page">
      <div className="region-header">
        <img src={logo} alt="SkyWind Logo" />
        <h2>Region Map</h2>
      </div>

      <div className="region-main">
        <div className="region-left">
          {regionDetails && (
            <div className="region-map-container">
              <RegionMap
                region={regionDetails}
                zones={zones}
                onZoneSelect={handleZoneClick}
              />
            </div>
          )}
        </div>

        <div className="region-right">
          <div className="details-card">
            <h2>Region Details</h2>
            {regionDetails && <RegionDetails region={regionDetails} />}
          </div>

          <div className="details-card">
            <h2>Zone Details</h2>
            {!selectedZone && <p className="zone-placeholder">Click a zone</p>}
            {selectedZone && <ZoneDetails zone={selectedZone} />}
          </div>

          <div className="details-card">
            <h2>Zone Power by Turbine</h2>

            <div style={{ marginBottom: "12px" }}>
              <label htmlFor="turbine-select" style={{ marginRight: "8px" }}>
                Turbine type:
              </label>
              <select
                id="turbine-select"
                value={selectedTurbineId}
                onChange={(e) => setSelectedTurbineId(Number(e.target.value))}
              >
                <option value={1}>Small Wind Turbine</option>
                <option value={2}>Utility-Scale Onshore Turbine</option>
                <option value={3}>Utility-Scale Offshore Turbine</option>
              </select>
            </div>

            {zonePowers.length === 0 ? (
              <p style={{ color: "var(--text-secondary)" }}>
                No power data available.
              </p>
            ) : (
              <div style={{ maxHeight: "260px", overflowY: "auto" }}>
                <table className="zone-power-table">
                  <thead>
                    <tr>
                      <th>Zone #</th>
                      <th>A</th>
                      <th>B</th>
                      <th>C</th>
                      <th>D</th>
                      <th>v (m/s)</th>
                      <th>ρ</th>
                      <th>Power</th>
                    </tr>
                  </thead>
                  <tbody>
                    {zonePowers.map((row) => (
                      <tr key={row.id}>
                        <td>{row.zone_index}</td>
                        <td>{row.A.lat.toFixed(4)}, {row.A.lon.toFixed(4)}</td>
                        <td>{row.B.lat.toFixed(4)}, {row.B.lon.toFixed(4)}</td>
                        <td>{row.C.lat.toFixed(4)}, {row.C.lon.toFixed(4)}</td>
                        <td>{row.D.lat.toFixed(4)}, {row.D.lon.toFixed(4)}</td>
                        <td>{row.avg_wind_speed.toFixed(2)}</td>
                        <td>{row.air_density.toFixed(3)}</td>
                        <td>{row.power_kw.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}