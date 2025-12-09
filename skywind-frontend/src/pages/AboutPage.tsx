import "./AboutPage.css";

/* import pozele reale */
import memberMadi from "../assets/member_madi.png";
import memberAle from "../assets/member_ale.png";
import memberAlexia from "../assets/member_alexia.png";
import memberBeatrice from "../assets/member_beatrice.png";
import memberRazvan from "../assets/member_razvan.png";
import memberStefan from "../assets/member_stefan.png";
import memberVlad from "../assets/member_vlad.png";

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
          <p>Analyzes elevation, roughness, and land classification.</p>
        </div>

        <div className="feature-card">
          <h3>🧠 Automated Data Preprocessing</h3>
          <p>Cleans, normalizes, and structures raw geospatial data for consistent analysis.</p>
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

      {/* ROW 1 (4 membri) */}
      <div className="team-grid-row team-row-1">

        <div className="team-card">
          <img src={memberMadi} alt="Mădălina" className="team-photo photo-mada" />
          <h3>Mădălina</h3>
          <p>Project Manager</p>
        </div>

        <div className="team-card">
          <img src={memberAle} alt="Alexandra" className="team-photo" />
          <h3>Alexandra</h3>
          <p>Frontend Lead Developer</p>
        </div>

        <div className="team-card">
          <img src={memberAlexia} alt="Alexia" className="team-photo" />
          <h3>Alexia</h3>
          <p>Data Processing Engineer & Frontend Developer</p>
        </div>

        <div className="team-card">
          <img src={memberBeatrice} alt="Beatrice" className="team-photo photo-bea" />
          <h3>Beatrice</h3>
          <p>Backend API Engineer</p>
        </div>

      </div>

      {/* ROW 2 (3 membri) */}
      <div className="team-grid-row team-row-2">
        <div className="team-card">
          <img src={memberRazvan} alt="Răzvan" className="team-photo" />
          <h3>Răzvan</h3>
          <p>Documentation & Frontend Workflow Support</p>
        </div>

        <div className="team-card">
          <img src={memberStefan} alt="Ștefan" className="team-photo" />
          <h3>Ștefan</h3>
          <p>DevOps Engineer & Database Admin</p>
        </div>

        <div className="team-card">
          <img src={memberVlad} alt="Vlad" className="team-photo" />
          <h3>Vlad</h3>
          <p>Backend API Engineer</p>
        </div>
      </div>

    </div>
  );
}