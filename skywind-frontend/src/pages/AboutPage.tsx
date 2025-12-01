import "./AboutPage.css";
import logo from "../assets/logo.png";
import memberImg from "../assets/member.png";

export default function AboutPage() {
  return (
    <div className="about-container">

      <h1 className="about-title">About SkyWind</h1>

      <p className="about-intro">
        SkyWind is a geospatial intelligence platform that analyzes wind potential,
        terrain suitability, and infrastructure proximity to help identify optimal
        locations for wind energy development.
      </p>

      <h2 className="section-title">Key Features</h2>

      <div className="features-grid">
        <div className="feature-card">
          <h3>⚡ Automated Region Generation</h3>
          <p>Builds a complete geospatial grid using only a coordinate input.</p>
        </div>

        <div className="feature-card">
          <h3>🌬 Satellite-Based Wind Analysis</h3>
          <p>Computes wind speed, density, turbulence, and energy potential.</p>
        </div>

        <div className="feature-card">
          <h3>⛰ Terrain Suitability Detection</h3>
          <p>Analyzes elevation, slope, roughness, and land classification.</p>
        </div>

        <div className="feature-card">
          <h3>🔌 Infrastructure Awareness</h3>
          <p>Finds the nearest energy storage or transmission nodes.</p>
        </div>

        <div className="feature-card">
          <h3>🗺 Interactive Grid Visualization</h3>
          <p>Explore each zone through a detailed map-based interface.</p>
        </div>

        <div className="feature-card">
          <h3>📊 Dynamic Suitability Scoring</h3>
          <p>Generates an environmental score from 0–100 for every zone.</p>
        </div>
      </div>

      <h2 className="section-title">Meet the Team</h2>

      <div className="team-grid-row team-row-1">
        <div className="team-card">
          <img src={memberImg} alt="member" className="team-photo" />
          <h3>Member 1</h3>
          <p>Role</p>
        </div>

        <div className="team-card">
          <img src={memberImg} alt="member" className="team-photo" />
          <h3>Member 2</h3>
          <p>Role</p>
        </div>

        <div className="team-card">
          <img src={memberImg} alt="member" className="team-photo" />
          <h3>Member 3</h3>
          <p>Role</p>
        </div>

        <div className="team-card">
          <img src={memberImg} alt="member" className="team-photo" />
          <h3>Member 4</h3>
          <p>Role</p>
        </div>
      </div>

      <div className="team-grid-row team-row-2">
        <div className="team-card">
          <img src={memberImg} alt="member" className="team-photo" />
          <h3>Member 5</h3>
          <p>Role</p>
        </div>

        <div className="team-card">
          <img src={memberImg} alt="member" className="team-photo" />
          <h3>Member 6</h3>
          <p>Role</p>
        </div>

        <div className="team-card">
          <img src={memberImg} alt="member" className="team-photo" />
          <h3>Member 7</h3>
          <p>Role</p>
        </div>
      </div>

    </div>
  );
}