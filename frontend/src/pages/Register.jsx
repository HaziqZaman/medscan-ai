import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import "./Login.css";

function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleChange = (e) => {
    if (isSubmitting || isSuccess) return;
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleRegister = async () => {
    if (isSubmitting || isSuccess) return;

    const name = form.name.trim();
    const email = form.email.trim();
    const password = form.password;
    const confirm = form.confirm;

    if (!name || !email || !password || !confirm) {
      toast.error("Please fill in all fields");
      return;
    }

    if (password !== confirm) {
      toast.error("Passwords do not match");
      return;
    }

    setIsSubmitting(true);
    const toastId = toast.loading("Creating your account...");

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setIsSuccess(true);
        toast.success("Registration successful", { id: toastId });

        setTimeout(() => {
          window.location.replace("/");
        }, 700);
      } else {
        let message = "Registration failed";

        if (typeof data.detail === "string") {
          message = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          message = data.detail[0]?.msg || message;
        }

        setIsSubmitting(false);
        toast.error(message, { id: toastId });
      }
    } catch (error) {
      console.error(error);
      setIsSubmitting(false);
      toast.error("Server connection error", { id: toastId });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleRegister();
    }
  };

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-brand">
          MedScan <span>AI</span>
        </div>

        <h1>
          Join the
          <br />
          <span>future</span> of
          <br />
          pathology.
        </h1>

        <p>
          Create your account and start exploring AI-powered breast cancer
          histopathology analysis.
        </p>

        <div className="login-tags">
          {[
            "IDC Breast Cancer Detection",
            "Tumor Grading",
            "A dedicated knowledge center for histopathology",
            "RAG based Chatbot for Medical Queries",
            "Grad-CAM Visual Explanations",
            "Educational Use Only",
          ].map((t) => (
            <div className="login-tag" key={t}>
              <div className="login-tag-dot" />
              <span>{t}</span>
            </div>
          ))}
        </div>
      </div>

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
              onKeyDown={handleKeyDown}
              disabled={isSubmitting || isSuccess}
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
              onKeyDown={handleKeyDown}
              disabled={isSubmitting || isSuccess}
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
              onKeyDown={handleKeyDown}
              disabled={isSubmitting || isSuccess}
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
              onKeyDown={handleKeyDown}
              disabled={isSubmitting || isSuccess}
            />
          </div>

          <button
            className={`login-btn ${isSuccess ? "is-success" : ""}`}
            onClick={handleRegister}
            disabled={isSubmitting || isSuccess}
          >
            {isSubmitting && !isSuccess ? (
              <span className="btn-content">
                <span className="btn-spinner" />
                <span>Creating Account...</span>
              </span>
            ) : isSuccess ? (
              <span className="btn-content">
                <span className="btn-check">✓</span>
                <span>Success</span>
              </span>
            ) : (
              <span className="btn-content">Create Account</span>
            )}
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