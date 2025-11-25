import { useState } from "react"; //Imports React’s useState hook
import { computeRegion } from "../services/RegionAPI"; //Imports your function that calls the backend'
import { useNavigate } from "react-router-dom"; //Hook from React Router -> Lets you navigate to another page programmatically
import type {RegionComputeResponseDTO } from "../dtos/RegionDetailsDTO.ts"; //shape of the backend response

//Loads static assets
//Vite transforms these into URLs at buildTime
//You can now use them as <img src={logo} />

import logo from "../assets/logo.svg";
import wallpaper from "../assets/wallpaper.png";

//Defines the HomePage React component
//export default means other files can import it freely

export default function HomePage() {
  const navigate = useNavigate();

  const [lat, setLat] = useState("");//initialized with empty string
  const [lon, setLon] = useState("");
  const [side, setSide] = useState("");
  const [zones, setZones] = useState("");

  //This function is triggered when the form is submitted
  //Marked async because we call await computeRegion(...)
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); //Prevents the browser’s default refresh

    const payload = {
      lat: parseFloat(lat),
      lon: parseFloat(lon),
      side_km: parseFloat(side),
      zones_per_edge: parseInt(zones),
    };

    const result: RegionComputeResponseDTO = await computeRegion(payload);
    navigate("/region", { state: result }); //redirect user to /region pqge
  }

  // PAGE LAYOUT - the component returns HTML-like JSX
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
          <h1 className="hero-title">Welcome to SkyWind</h1>
          <p className="hero-subtitle">
            Compute renewable-energy potential for any region on Earth.
          </p>
        </div>
      </div>

      {/* FORM SECTION */}
      <div className="form-section">
        <h2 className="form-title">Get Info for a Region</h2>

        <form
          onSubmit={handleSubmit} //triggers the function you wrote
          style={{ display: "flex", flexDirection: "column", gap: "15px" }} //flexbox layout
        >
          <input
            className="input-field"
            type="number"
            placeholder="Latitude"
            value={lat}  //react state
            onChange={(e) => setLat(e.target.value)} //update the state
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
