import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import "./Login.css";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleChange = (e) => {
    if (isSubmitting || isSuccess) return;
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async () => {
    if (isSubmitting || isSuccess) return;

    const email = form.email.trim();
    const password = form.password;

    if (!email || !password) {
      toast.error("Please enter email and password");
      return;
    }

    setIsSubmitting(true);
    const toastId = toast.loading("Signing you in...");

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.access_token);

        if (data.user) {
          localStorage.setItem("user", JSON.stringify(data.user));
        }

        setIsSuccess(true);
        toast.success("Login successful", { id: toastId });

        setTimeout(() => {
          window.location.replace("/landing");
        }, 700);
      } else {
        setIsSubmitting(false);
        toast.error(data.detail || "Login failed", { id: toastId });
      }
    } catch (error) {
      console.error(error);
      setIsSubmitting(false);
      toast.error("Server connection error", { id: toastId });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleLogin();
    }
  };

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-brand">
          MedScan <span>AI</span>
        </div>

        <h1>
          Learn about cancer
          <br />
          with <span>help</span>
          <br />
          of Artificial Intelligence
        </h1>

        <p>
          An educational platform for medical students and trainees to understand
          AI-driven histopathology analysis.
        </p>

        <div className="login-tags">
          {[
            "IDC Breast Cancer Detection",
            "Cancer Cells Grading",
            "A dedicated knowledge center for histopathology",
            "RAG based Chatbot for Medical Queries",
            "Educational Use Only (Non-Clinical Tool)",
          ].map((tag) => (
            <div className="login-tag" key={tag}>
              <div className="login-tag-dot" />
              <span>{tag}</span>
            </div>
          ))}
        </div>
      </div>

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
              onKeyDown={handleKeyDown}
              disabled={isSubmitting || isSuccess}
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
              onKeyDown={handleKeyDown}
              disabled={isSubmitting || isSuccess}
            />
          </div>

          <button
            className={`login-btn ${isSuccess ? "is-success" : ""}`}
            onClick={handleLogin}
            disabled={isSubmitting || isSuccess}
          >
            {isSubmitting && !isSuccess ? (
              <span className="btn-content">
                <span className="btn-spinner" />
                <span>Signing In...</span>
              </span>
            ) : isSuccess ? (
              <span className="btn-content">
                <span className="btn-check">✓</span>
                <span>Success</span>
              </span>
            ) : (
              <span className="btn-content">Sign In</span>
            )}
          </button>

          <div className="login-divider">or</div>

          <div className="login-register">
            Don't have an account? <Link to="/register">Register here</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;