import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import logo from "../assets/logo.svg";

import RegionMap from "../components/RegionMap";
import RegionDetails from "../components/RegionDetails";
import ZoneDetails from "../components/ZoneDetails";

import { getRegionDetails, getRegionZones, getZoneDetails } from "../services/RegionAPI.ts";

import type { RegionDetailsDTO } from "../dtos/RegionDetailsDTO";
import type { ZoneDetailsDTO } from "../dtos/ZoneDetailsDTO";

export default function RegionPage() {
  const { state } = useLocation();
  const navigate = useNavigate();

  const regionId = state?.region_id ?? null;

  const [regionDetails, setRegionDetails] = useState<RegionDetailsDTO | null>(null);
  const [zones, setZones] = useState<ZoneDetailsDTO[]>([]);
  const [selectedZone, setSelectedZone] = useState<ZoneDetailsDTO | null>(null);

  // --------------------------
  // LOAD REGION + ZONES
  // --------------------------
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

  // --------------------------
  // HANDLE ZONE CLICK
  // --------------------------
  async function handleZoneClick(zoneId: number) {
    const fullZone = await getZoneDetails(zoneId);
    setSelectedZone(fullZone);
  }

  // --------------------------
  // EARLY RETURN (SAFE NOW)
  // --------------------------
  if (!regionId) {
    return (
      <div className="region-page">
        <p>No region data. Please compute a region first.</p>
        <button onClick={() => navigate("/")}>Back</button>
      </div>
    );
  }

return (
  <div className="region-page">
    {/* HEADER */}
    <div className="region-header">
      <img src={logo} alt="SkyWind Logo" />
      <h2>Region Map</h2>
    </div>

    {/* MAIN TWO-COLUMN LAYOUT */}
    <div className="region-main">
      {/* LEFT = MAP */}
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

      {/* RIGHT = REGION + ZONE DETAILS */}
      <div className="region-right">
        <div className="details-card">
          <h2>Region Details</h2>
          {regionDetails && <RegionDetails region={regionDetails} />}
        </div>

        <div className="details-card">
          <h2>Zone Details</h2>
          {!selectedZone && (
            <p className="zone-placeholder">Click a zone</p>
          )}
          {selectedZone && <ZoneDetails zone={selectedZone} />}
        </div>
      </div>
    </div>
  </div>
);


}
