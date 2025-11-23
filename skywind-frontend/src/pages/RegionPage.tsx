import { useLocation, useNavigate } from "react-router-dom";
//useLocation() → retrieves data passed from navigate("/region", { state })
//useNavigate() → lets you redirect programmatically back to Home

import { useState } from "react";//Lets you store internal component state
import logo from "../assets/logo.svg";
import RegionMap from "../components/RegionMap";
import type { RegionComputeResponseDTO } from "../dtos/RegionComputeResponseDTO";

export default function RegionPage() {
  const { state } = useLocation();//Reads the region data passed from HomePage
  const navigate = useNavigate();//Allows redirecting to home when needed

  const region = state as RegionComputeResponseDTO | null;
  const [selectedZone, setSelectedZone] = useState<any>(null); //Initially, no zone is selected

  if (!region) {
    return (
      <div className="region-page">
        <p>No region data. Please compute a region first.</p>
        <button onClick={() => navigate("/")}>Back</button>
      </div>
    );
  }

  // AUTO-FORMAT JSON OBJECTS FUNCTION
  function renderFormattedJSON(obj: any) {
    return (
      <div className="json-table">
        {Object.entries(obj).map(([key, value]) => {
          //Object.entries() → converts object to array of [key, value]
          //.map() → iterate each key/value pair and return JSX

          // Nested objects like A, B, C, D
          if (typeof value === "object" && value !== null) {
            return (
              <div key={key} className="json-block">
                <div className="json-key">{key}:</div>
                <div className="json-sub">
                  {Object.entries(value).map(([subKey, subValue]) => (
                    <div key={subKey} className="json-line">
                      <span className="json-subkey">{subKey}</span>: {String(subValue)}
                    </div>
                  ))}
                </div>
              </div>
            );
          }

          // Simple values
          return (
            <div key={key} className="json-line">
              <span className="json-key">{key}</span>: {String(value)}
            </div>
          );
        })}
      </div>
    );
  }

  // PAGE LAYOUT
  return (
    <div className="region-page">

      {/* LEFT SIDE */}
      <div className="region-left">
        <div className="region-header">
          <img src={logo} alt="SkyWind Logo" />
          <h2>Region Map</h2>
        </div>

        <div className="region-map-container">
          <RegionMap region={region} onZoneSelect={setSelectedZone} />
        </div>
      </div>

      {/* RIGHT SIDE */}
      <div className="region-right">

        {/* REGION INFO */}
        <h2>Region Details</h2>
        <div className="region-info">
          <div className="region-group">
            <h4>Center</h4>
            <p className="region-line"><strong>Lat:</strong> {region.center.lat.toFixed(4)}</p>
            <p className="region-line"><strong>Lon:</strong> {region.center.lon.toFixed(4)}</p>
          </div>

          <div className="region-group">
            <h4>Corners</h4>
            <p className="region-line"><strong>A:</strong> {region.corners.A.lat.toFixed(4)}, {region.corners.A.lon.toFixed(4)}</p>
            <p className="region-line"><strong>B:</strong> {region.corners.B.lat.toFixed(4)}, {region.corners.B.lon.toFixed(4)}</p>
            <p className="region-line"><strong>C:</strong> {region.corners.C.lat.toFixed(4)}, {region.corners.C.lon.toFixed(4)}</p>
            <p className="region-line"><strong>D:</strong> {region.corners.D.lat.toFixed(4)}, {region.corners.D.lon.toFixed(4)}</p>
          </div>
        </div>

        {/* ZONE INFO */}
        <h2 style={{ marginTop: "20px" }}>Zone Details</h2>

        {!selectedZone && (
          <p className="zone-placeholder">Click a zone</p>
        )}

        {selectedZone && (
          <div className="zone-info">
            <h3>Zone {selectedZone.index}</h3>
            {renderFormattedJSON(selectedZone)}
          </div>
        )}

      </div>
    </div>
  );
}
