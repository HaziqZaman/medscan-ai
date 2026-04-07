import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

function Navbar() {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/analysis",  label: "Analysis"  },
    { to: "/history",   label: "History"   },
    { to: "/knowledge", label: "Knowledge" },
    { to: "/chatbot",   label: "AI Assistant" },
    { to: "/about",     label: "About"     },
  ];

  const handleLogout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.replace("/");
};

  const closeMenu = () => setMenuOpen(false);

  return (
    <>
      <nav className="navbar">
        {/* Logo */}
        <Link to="/landing" className="navbar-logo" onClick={closeMenu}>
          <span className="logo-icon">🔬</span>
          MedScan <span>AI</span>
        </Link>

        {/* Desktop links */}
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
          <button className="nav-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>

        {/* Hamburger (mobile) */}
        <button
          className={`nav-hamburger ${menuOpen ? "open" : ""}`}
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-label="Toggle menu"
        >
          <span />
          <span />
          <span />
        </button>
      </nav>

      {/* Mobile drawer */}
      <div className={`navbar-mobile-menu ${menuOpen ? "open" : ""}`}>
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className={`nav-link ${location.pathname === link.to ? "active" : ""}`}
            onClick={closeMenu}
          >
            {link.label}
          </Link>
        ))}
        <button className="nav-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </>
  );
}

export default Navbar;