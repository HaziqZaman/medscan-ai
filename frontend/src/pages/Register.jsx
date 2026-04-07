import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Login.css";

function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: ""
  });
  const navigate = useNavigate();

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleRegister = async () => {
    if (!form.name.trim() || !form.email.trim() || !form.password.trim() || !form.confirm.trim()) {
      alert("Please fill in all fields");
      return;
    }

    if (form.password !== form.confirm) {
      alert("Passwords do not match");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password
        })
      });

      const data = await response.json();

      if (response.ok) {
        alert("Registration successful");
        navigate("/");
      } else {
        let message = "Registration failed";

        if (typeof data.detail === "string") {
          message = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          message = data.detail[0]?.msg || message;
        }

        alert(message);
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
        <h1>Join the<br /><span>future</span> of<br />pathology.</h1>
        <p>
          Create your account and start exploring AI-powered breast cancer
          histopathology analysis.
        </p>

        <div className="login-tags">
          {[
            "IDC Breast Cancer Detection",
            "Tumor Grading with ResNet-18",
            "Grad-CAM Visual Explanations",
            "Educational Use Only"
          ].map((t) => (
            <div className="login-tag" key={t}>
              <div className="login-tag-dot" />
              <span>{t}</span>
            </div>
          ))}
        </div>
      </div>

      {/* RIGHT */}
      <div className="login-right">
        <div className="login-form-container">
          <div className="login-edu-badge">Educational Platform</div>
          <h2>Create account</h2>
          <p>Join MedScan AI as a student or trainee</p>

          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              name="name"
              placeholder="Your full name"
              value={form.name}
              onChange={handleChange}
            />
          </div>

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
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              name="confirm"
              placeholder="••••••••"
              value={form.confirm}
              onChange={handleChange}
            />
          </div>

          <button className="login-btn" onClick={handleRegister}>
            Create Account
          </button>

          <div className="login-register" style={{ marginTop: "1.25rem" }}>
            Already have an account?{" "}
            <Link
              to="/"
              style={{ color: "#17c964", fontWeight: 700, textDecoration: "none" }}
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register;