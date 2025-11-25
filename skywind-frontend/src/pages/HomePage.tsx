import { useState } from "react"; //Imports React’s useState hook
import { computeRegion } from "../services/RegionAPI"; //Imports your function that calls the backend'
import { useNavigate } from "react-router-dom"; //Hook from React Router -> Lets you navigate to another page programmatically
import type {RegionComputeResponseDTO } from "../dtos/RegionDetailsDTO.ts"; //shape of the backend response

//Loads static assets
//Vite transforms these into URLs at buildTime
//You can now use them as <img src={logo} />

import logo from "../assets/logo.svg";
import wallpaper from "../assets/wallpaper.png";

interface FormErrors {
  lat?: string;
  lon?: string;
  side?: string;
  zones?: string;
}

export default function HomePage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [side, setSide] = useState("20");
  const [zones, setZones] = useState("10");
  
  const [errors, setErrors] = useState<FormErrors>({});

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!lat || isNaN(parseFloat(lat))) {
      newErrors.lat = "Valid latitude is required";
    } else {
      const latNum = parseFloat(lat);
      if (latNum < -90 || latNum > 90) {
        newErrors.lat = "Latitude must be between -90 and 90";
      }
    }

    if (!lon || isNaN(parseFloat(lon))) {
      newErrors.lon = "Valid longitude is required";
    } else {
      const lonNum = parseFloat(lon);
      if (lonNum < -180 || lonNum > 180) {
        newErrors.lon = "Longitude must be between -180 and 180";
      }
    }

    if (!side || isNaN(parseFloat(side)) || parseFloat(side) <= 0) {
      newErrors.side = "Side length must be a positive number";
    }

    if (!zones || isNaN(parseInt(zones)) || parseInt(zones) <= 0) {
      newErrors.zones = "Zones per edge must be a positive integer";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      const payload = {
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        side_km: parseFloat(side),
        zones_per_edge: parseInt(zones),
      };

      const result: RegionComputeResponseDTO = await computeRegion(payload);
      navigate("/region", { state: result });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to compute region. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
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
          <img src={logo} alt="SkyWind" />
          <h1 className="hero-title">Welcome to SkyWind</h1>
          <p className="hero-subtitle">
            Discover optimal wind farm locations using satellite data and advanced
            geospatial analysis. Compute renewable energy potential for any region on Earth.
          </p>
        </div>
      </div>

      {/* FORM SECTION */}
      <div className="form-section">
        <div className="form-card">
          <h2 className="form-title">Analyze a Region</h2>
          <p className="form-subtitle">
            Enter coordinates and parameters to compute wind energy potential
          </p>

          {error && (
            <div
              style={{
                padding: "12px 16px",
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid #ef4444",
                borderRadius: "8px",
                color: "#ef4444",
                marginBottom: "20px",
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Latitude *</label>
                <input
                  className={`input-field ${errors.lat ? "input-error" : ""}`}
                  type="number"
                  step="any"
                  placeholder="e.g., 46.77"
                  value={lat}
                  onChange={(e) => {
                    setLat(e.target.value);
                    if (errors.lat) setErrors({ ...errors, lat: undefined });
                  }}
                  disabled={isLoading}
                />
                {errors.lat && (
                  <span className="error-message">{errors.lat}</span>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Longitude *</label>
                <input
                  className={`input-field ${errors.lon ? "input-error" : ""}`}
                  type="number"
                  step="any"
                  placeholder="e.g., 23.62"
                  value={lon}
                  onChange={(e) => {
                    setLon(e.target.value);
                    if (errors.lon) setErrors({ ...errors, lon: undefined });
                  }}
                  disabled={isLoading}
                />
                {errors.lon && (
                  <span className="error-message">{errors.lon}</span>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Side Length (km) *</label>
                <input
                  className={`input-field ${errors.side ? "input-error" : ""}`}
                  type="number"
                  step="any"
                  placeholder="e.g., 20"
                  value={side}
                  onChange={(e) => {
                    setSide(e.target.value);
                    if (errors.side) setErrors({ ...errors, side: undefined });
                  }}
                  disabled={isLoading}
                />
                {errors.side && (
                  <span className="error-message">{errors.side}</span>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Zones per Edge *</label>
                <input
                  className={`input-field ${errors.zones ? "input-error" : ""}`}
                  type="number"
                  placeholder="e.g., 10"
                  value={zones}
                  onChange={(e) => {
                    setZones(e.target.value);
                    if (errors.zones)
                      setErrors({ ...errors, zones: undefined });
                  }}
                  disabled={isLoading}
                />
                {errors.zones && (
                  <span className="error-message">{errors.zones}</span>
                )}
              </div>
            </div>

            <button
              className="submit-btn"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="loading-spinner"></span>
                  Computing...
                </>
              ) : (
                "Compute Region"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
