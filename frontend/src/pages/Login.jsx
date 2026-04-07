import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Login.css";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email: form.email,
          password: form.password
        })
      });

      const data = await response.json();

      if (response.ok) {
        // Save JWT token
        localStorage.setItem("token", data.access_token);

        alert("Login successful");

        // Redirect to landing/dashboard
        window.location.href = "/landing";

      } else {
        alert(data.detail || "Login failed");
      }

    } catch (error) {
      console.error(error);
      alert("Server connection error");
    }
  };

  return (
    <div className="login-page">

      {/* LEFT */}
      <div className="login-left">
        <div className="login-brand">MedScan <span>AI</span></div>

        <h1>Learn about cancer<br />with <span>help</span><br />of Artificial Intelligence</h1>

        <p>
          An educational platform for medical students and trainees to understand
          AI-driven histopathology analysis.
        </p>

        <div className="login-tags">
          {[
            "IDC Breast Cancer Detection",
            "Cancer Cells Grading",
            "LVI Tissues Analysis",
            "RAG based Chatbot for Medical Queries",
            "Educational Use Only(Non-Clinical Tool)",
          ].map((tag) => (
            <div className="login-tag" key={tag}>
              <div className="login-tag-dot" />
              <span>{tag}</span>
            </div>
          ))}
        </div>
      </div>

      {/* RIGHT */}
      <div className="login-right">
        <div className="login-form-container">

          <div className="login-edu-badge">Educational Platform</div>

          <h2>Welcome back</h2>
          <p>Sign in to your MedScan AI account</p>

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              placeholder="student@university.edu"
              value={form.email}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              placeholder="********"
              value={form.password}
              onChange={handleChange}
            />
          </div>

          <button className="login-btn" onClick={handleLogin}>
            Sign In
          </button>

          <div className="login-divider">or</div>

          <div className="login-register">
            Don't have an account?{" "}
            <Link to="/register">Register here</Link>
          </div>

        </div>
      </div>

    </div>
  );
}

export default Login;