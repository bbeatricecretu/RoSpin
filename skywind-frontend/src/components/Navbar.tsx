import { Link, NavLink } from "react-router-dom";
import "./Navbar.css";
import logo from "../assets/logo.png"; // pune logo-ul tău în assets/

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-left">
        <img src={logo} className="nav-logo" alt="SkyWind logo" />
        <span className="nav-title">SkyWind</span>
      </div>

      <div className="nav-links">
        <NavLink to="/" className="nav-link">
          Home
        </NavLink>

        <NavLink to="/generate" className="nav-link">
          Generate Region
        </NavLink>

        <NavLink to="/saved" className="nav-link">
          Saved Regions
        </NavLink>

        <NavLink to="/about" className="nav-link">
          About
        </NavLink>

        <NavLink to="/contact" className="nav-link">
          Contact
        </NavLink>
      </div>
    </nav>
  );
}