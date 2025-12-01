import "./HomePage.css";
import logo from "../assets/logo.png";
import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <div className="home-container">

      <div className="home-hero">
        <img src={logo} alt="SkyWind Logo" className="home-logo" />

        <h1 className="home-title">SkyWind</h1>
        <p className="home-subtitle">
          Optimizing wind energy through geographical analysis and smart grid forecasting.
        </p>

        <Link to="/generate" className="home-cta">
          Generate a New Region
        </Link>
      </div>

    </div>
  );
}