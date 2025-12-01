import "./HomePage.css";
import logo from "../assets/logo.png";
import windBg from "../assets/wind-bg.png";
import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <div className="home-wrapper">

      {/* Background image (subtle, faded) */}
      <img src={windBg} alt="" className="home-bg" />

      <div className="home-content">
        <img src={logo} alt="SkyWind Logo" className="home-logo" />

        <h1 className="home-title">SkyWind</h1>

        <p className="home-subtitle">
          Intelligent wind-energy modeling powered by geographical analytics.
        </p>

        <Link to="/generate" className="home-button">
          Generate a New Region
        </Link>

        <div className="home-benefits">
          <div className="benefit">
            <span className="benefit-icon">🧭</span>
            <h3>Geospatial Precision</h3>
            <p>Analyze real-world wind data with high-accuracy regional grids.</p>
          </div>

          <div className="benefit">
            <span className="benefit-icon">⚡</span>
            <h3>Energy Forecast</h3>
            <p>Predict zone-level wind energy production instantly.</p>
          </div>

          <div className="benefit">
            <span className="benefit-icon">🌍</span>
            <h3>Eco-Optimized</h3>
            <p>Designed for sustainable energy planning and smart grid systems.</p>
          </div>
        </div>
      </div>
    </div>
  );
}