import { Link, useLocation } from "react-router-dom";
import logo from "../assets/logo.svg";

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <Link to="/" className="navbar-brand">
          <img src={logo} alt="SkyWind Logo" />
          <span>SkyWind</span>
        </Link>
        <div className="navbar-links">
          <Link
            to="/"
            className={`navbar-link ${location.pathname === "/" ? "active" : ""}`}
          >
            Home
          </Link>
        </div>
      </div>
    </nav>
  );
}

