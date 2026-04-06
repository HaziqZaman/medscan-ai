import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

function Navbar() {
  const location = useLocation();

  const links = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/analysis", label: "Analysis" },
    { to: "/history", label: "History" },
    { to: "/knowledge", label: "Knowledge" },
    { to: "/chatbot", label: "AI Assistant" },
    { to: "/about", label: "About" },
  ];

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-logo">
        MedScan <span>AI</span>
      </Link>
      <div className="navbar-links">
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className={`nav-link ${location.pathname === link.to ? "active" : ""}`}
          >
            {link.label}
          </Link>
        ))}
        <button className="nav-logout" onClick={() => {
          localStorage.removeItem("token");
          window.location.href = "/";
        }}>
          Logout
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
