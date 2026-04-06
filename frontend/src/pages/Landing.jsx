import { Link } from "react-router-dom";
import "../styles.css";
import "./Landing.css";
import analysisImage from "../assets/images/23.png";
import botImage from "../assets/images/56.png";

function Landing() {
  return (
    <div className="landing-page">
      <div className="landing-container">
        
        {/* TOP NAV OVERLAY */}
        <div className="landing-navbar">
          <div className="logo">
            MedScan AI
          </div>
          <div className="nav-links">
            <Link to="/dashboard">Dashboard</Link>
            <span>Logout</span>
          </div>
        </div>

        {/* MAIN SPLIT AREA */}
        <div className="landing-panels">
          
          {/* LEFT PANEL */}
          <div className="landing-left">
            <h2 className="panel-title">Image Analysis</h2>
            <p className="panel-subtitle">Educational</p>
            <img
              src={analysisImage}
              alt="AI Analysis"
              className="landing-image"
            />
            <Link to="/analysis">
              <button className="primary-btn">
                Start Analysis
              </button>
            </Link>
          </div>

          {/* RIGHT PANEL */}
          <div className="landing-right">
            <h2 className="panel-title">AI Assistant</h2>
            <p className="panel-subtitle">Guide</p>
            <img
              src={botImage}
              alt="AI Assistant"
              className="landing-image"
            />
            <Link to="/chatbot">
              <button className="secondary-btn">
                Chat with AI
              </button>
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Landing;