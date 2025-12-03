import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";
import "./RegionPage.css";

import RegionMap from "../components/RegionMap";
import RegionDetails from "../components/RegionDetails";
import ZoneDetails from "../components/ZoneDetails";

import {
  getRegionDetails,
  getRegionZones,
  getZoneDetails,
  getRegionZonePowers,
} from "../services/RegionAPI";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";


// ==============================
// TURBINE TYPES
// ==============================
const TURBINES = [
  { id: 1, name: "Small Turbine (50m rotor)" },
  { id: 2, name: "Onshore Turbine (100m rotor)" },
  { id: 3, name: "Offshore Turbine (150m rotor)" },
];

export default function RegionPage() {
  const { state } = useLocation();
  const navigate = useNavigate();

  const regionId = state?.region_id ?? null;

  const [region, setRegion] = useState<RegionDetailsDTO | null>(null);
  const [zones, setZones] = useState<ZoneDetailsDTO[]>([]);
  const [selectedZone, setSelectedZone] = useState<ZoneDetailsDTO | null>(null);

  const [selectedTurbine, setSelectedTurbine] = useState<number>(1);
  const [powerRows, setPowerRows] = useState<any[]>([]);

  const [saved, setSaved] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"zone" | "power" | "top" | "export">("zone");

  // === NEW: loading states ===
  const [loadingRegion, setLoadingRegion] = useState(true);
  const [loadingZones, setLoadingZones] = useState(true);


  // --------------------------------------
  // LOAD REGION DATA
  // --------------------------------------
  useEffect(() => {
    if (!regionId) return;

    async function loadRegion() {
      setLoadingRegion(true);
      const r = await getRegionDetails(regionId);
      setRegion(r);

      // tiny delay so UI doesn't flicker
      setTimeout(() => setLoadingRegion(false), 300);
    }

    loadRegion();
  }, [regionId]);


  // --------------------------------------
  // LOAD ZONES DATA
  // --------------------------------------
  useEffect(() => {
    if (!regionId) return;

    async function loadZones() {
      setLoadingZones(true);
      const z = await getRegionZones(regionId);
      setZones(z);

      setTimeout(() => setLoadingZones(false), 300);
    }

    loadZones();
  }, [regionId]);


  // --------------------------------------
  // LOAD POWER ROWS
  // --------------------------------------
  useEffect(() => {
    if (!regionId) return;

    async function loadPower() {
      const rows = await getRegionZonePowers(regionId, selectedTurbine);
      setPowerRows(rows);
    }

    loadPower();
  }, [regionId, selectedTurbine]);


  // --------------------------------------
  // TOP 5 ZONES
  // --------------------------------------
  const top5 = useMemo(() => {
    return [...zones].sort((a, b) => b.potential - a.potential).slice(0, 5);
  }, [zones]);


  // --------------------------------------
  // SAVE REGION
  // --------------------------------------
  function toggleSave() {
    const savedList = JSON.parse(localStorage.getItem("savedRegions") || "[]");

    if (saved) {
      const filtered = savedList.filter((id: number) => id !== regionId);
      localStorage.setItem("savedRegions", JSON.stringify(filtered));
      setSaved(false);
    } else {
      savedList.push(regionId);
      localStorage.setItem("savedRegions", JSON.stringify(savedList));
      setSaved(true);
    }
  }

  useEffect(() => {
    const savedList = JSON.parse(localStorage.getItem("savedRegions") || "[]");
    setSaved(savedList.includes(regionId));
  }, [regionId]);


  // --------------------------------------
  // EXPORT JSON + CSV
  // --------------------------------------
  function exportJSON() {
    const data = { region, zones };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `region_${regionId}.json`;
    a.click();
  }


  function exportCSV(region: RegionDetailsDTO, zones: ZoneDetailsDTO[]) {
    if (!region || !zones || zones.length === 0) {
      alert("No region data available for CSV export.");
      return;
    }

    let csv = "Zone ID,Potential,Avg Wind Speed,Wind Direction,Min Alt,Max Alt,Roughness,Air Density,Power Avg,Land Type\n";

    zones.forEach(z => {
      csv += [
        z.id,
        z.potential,
        z.avg_wind_speed,
        z.wind_direction,
        z.min_alt,
        z.max_alt,
        z.roughness,
        z.air_density,
        z.power_avg,
        z.land_type.replace(',', ';')
      ].join(",") + "\n";
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `region_${region.id}_zones.csv`;
    a.click();

    URL.revokeObjectURL(url);
  }


  // --------------------------------------
  // NO REGION SENT
  // --------------------------------------
  if (!regionId)
    return (
      <div className="no-region">
        <h2>No Region Selected</h2>
        <button onClick={() => navigate("/generate")}>Generate Region</button>
      </div>
    );


  // --------------------------------------
  // NEW: REGION LOADING SCREEN
  // --------------------------------------
  if (loadingRegion) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading region data...</p>
      </div>
    );
  }


  // --------------------------------------
  // PAGE CONTENT
  // --------------------------------------
  return (
    <div className="region-layout">

      {/* HEADER BAR */}
      <div className="region-headerbox">
        <h1>Region Overview</h1>

        <button className={`save-btn ${saved ? "saved" : ""}`} onClick={toggleSave}>
          {saved ? "★ Saved" : "☆ Save"}
        </button>
      </div>


      {/* OVERVIEW */}
      {region && (
        <div className="overview-box">
          <div>
            <h3>Average Potential</h3>
            <p>{region.avg_potential.toFixed(1)} / 100</p>
          </div>
          <div>
            <h3>Region Rating</h3>
            <p>{region.rating.toFixed(1)}</p>
          </div>
          <div>
            <h3>Air Density</h3>
            <p>{region.index_average.toFixed(3)}</p>
          </div>
          <div>
            <h3>Max Zone</h3>
            <p>#{region.max_potential_zone}</p>
          </div>
        </div>
      )}


      {/* MAIN CONTENT */}
      <div className="region-content">

        {/* LEFT MAP SIDE */}
        <div className="map-side">

          {/* === ZONES LOADING OVERLAY === */}
          {loadingZones && (
            <div className="zones-loading-overlay">
              <div className="spinner"></div>
              <p>Loading map zones...</p>
            </div>
          )}

          <RegionMap
            region={region!}
            zones={zones}
            onZoneSelect={async (id) => {
              const z = await getZoneDetails(id);
              setSelectedZone(z);
              setActiveTab("zone");
            }}
          />

          {!loadingZones && (
            <div className="legend">
              <strong>Legend (Potential)</strong>

              <div className="legend-item">
                <span className="legend-color legend-low"></span>
                0–20 (Very Low)
              </div>

              <div className="legend-item">
                <span className="legend-color legend-low-med"></span>
                20–40 (Low)
              </div>

              <div className="legend-item">
                <span className="legend-color legend-med"></span>
                40–60 (Medium)
              </div>

              <div className="legend-item">
                <span className="legend-color legend-good"></span>
                60–80 (Good)
              </div>

              <div className="legend-item">
                <span className="legend-color legend-excellent"></span>
                80–100 (Excellent)
              </div>
            </div>
          )}
        </div>


        {/* RIGHT PANEL */}
        <div className="right-panel">

          <div className="tab-bar">
            <button onClick={() => setActiveTab("zone")} className={activeTab === "zone" ? "active" : ""}>
              Zone Details
            </button>
            <button onClick={() => setActiveTab("power")} className={activeTab === "power" ? "active" : ""}>
              Power Output
            </button>
            <button onClick={() => setActiveTab("top")} className={activeTab === "top" ? "active" : ""}>
              Top 5
            </button>
            <button onClick={() => setActiveTab("export")} className={activeTab === "export" ? "active" : ""}>
              Export
            </button>
          </div>


          {/* TABS CONTENT */}
          {activeTab === "zone" && (
            <div className="panel-card">
              {!selectedZone && <p>Select a zone from the map.</p>}
              {selectedZone && <ZoneDetails zone={selectedZone} />}
            </div>
          )}

          {activeTab === "power" && (
            <div className="panel-card">
              <h3>Turbine Power</h3>

              <select
                value={selectedTurbine}
                onChange={(e) => setSelectedTurbine(Number(e.target.value))}
              >
                {TURBINES.map((t) =>
                  <option key={t.id} value={t.id}>{t.name}</option>
                )}
              </select>

              <table className="power-table">
                <thead>
                  <tr>
                    <th>Zone</th>
                    <th>Wind (m/s)</th>
                    <th>ρ</th>
                    <th>kW</th>
                  </tr>
                </thead>
                <tbody>
                  {powerRows.map((r) => (
                    <tr key={r.id}>
                      <td>{r.zone_index}</td>
                      <td>{r.avg_wind_speed.toFixed(2)}</td>
                      <td>{r.air_density.toFixed(3)}</td>
                      <td>{r.power_kw.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "top" && (
            <div className="panel-card">
              <h3>Top 5 Zones</h3>

              <ul className="top-list">
                {top5.map((z) => (
                  <li
                    key={z.id}
                    onClick={async () => {
                      const full = await getZoneDetails(z.id);
                      setSelectedZone(full);
                      setActiveTab("zone");
                    }}
                  >
                    <strong>#{z.zone_index}</strong> — {z.potential.toFixed(1)} / 100
                  </li>
                ))}
              </ul>
            </div>
          )}

          {activeTab === "export" && (
            <div className="panel-card export-panel">
              <h3>Export Data</h3>

              <div className="export-buttons">
                <button className="export-btn" onClick={exportJSON}>Export JSON</button>
                <button className="export-btn" onClick={() => region && exportCSV(region, zones)}>Export CSV</button>
              </div>
            </div>
          )}

        </div>
      </div>

    </div>
  );
}