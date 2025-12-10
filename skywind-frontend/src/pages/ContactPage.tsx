import "./ContactPage.css";
import logo from "../assets/logo.png";

export default function ContactPage() {
  return (
    <div className="contact-container">

      <div className="contact-header">
        <img src={logo} alt="SkyWind Logo" className="contact-logo" />
        <h1 className="contact-title">Get in Touch</h1>
        <p className="contact-subtitle">
          Contact our team for collaboration, support, or project inquiries.
        </p>
      </div>

      <div className="contact-cards">

        {/* Row 1 – 3 cards */}
        <div className="contact-row">

          <div className="contact-card">
            <h3>Email</h3>
            <p>skywind.app.team@gmail.com</p>
          </div>

          <div className="contact-card">
            <h3>Phone</h3>
            <p>+40 722 253 931</p>
          </div>

          <div className="contact-card">
            <h3>GitHub</h3>
            <a
              className="contact-link"
              href="https://github.com/bbeatricecretu/RoSpin"
              target="_blank"
            >
              github.com/bbeatricecretu/RoSpin
            </a>
          </div>

        </div>

        {/* Row 2 – 2 cards */}
        <div className="contact-row">

          <div className="contact-card">
            <h3>Location</h3>
            <p>Cluj-Napoca, Romania</p>
          </div>

          <div className="contact-card">
            <h3>Availability</h3>
            <p>Mon–Fri, 10:00 – 18:00 (GMT+2)</p>
          </div>

        </div>

      </div>

    </div>
  );
}