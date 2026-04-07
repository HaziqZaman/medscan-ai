import { useEffect, useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import "./Dashboard.css";

function Dashboard() {
  const [summary, setSummary] = useState({
    total_analyses: 0,
    idc_detected: 0,
    non_idc: 0,
    avg_confidence: 0,
    recent_analyses: [],
  });

  const [user, setUser] = useState({
    name: "Student",
    email: "",
    role: "",
  });

  const [now, setNow] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError("");

        const token = localStorage.getItem("token");

        if (!token) {
          throw new Error("You are not logged in. Please log in first.");
        }

        const [summaryRes, profileRes] = await Promise.all([
          fetch("http://127.0.0.1:8000/cases/dashboard/summary", {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }),
          fetch("http://127.0.0.1:8000/user/profile", {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }),
        ]);

        const summaryData = await summaryRes.json();
        const profileData = await profileRes.json();

        if (!summaryRes.ok) {
          throw new Error(summaryData.detail || "Failed to load dashboard summary");
        }

        if (!profileRes.ok) {
          throw new Error(profileData.detail || "Failed to load user profile");
        }

        setSummary({
          total_analyses: summaryData.total_analyses ?? 0,
          idc_detected: summaryData.idc_detected ?? 0,
          non_idc: summaryData.non_idc ?? 0,
          avg_confidence: summaryData.avg_confidence ?? 0,
          recent_analyses: summaryData.recent_analyses ?? [],
        });

        setUser({
          name: profileData.name || "Student",
          email: profileData.email || "",
          role: profileData.role || "",
        });
      } catch (err) {
        console.error(err);
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const hour = now.getHours();

  let greeting = "Good evening";
  if (hour < 12) {
    greeting = "Good morning";
  } else if (hour < 18) {
    greeting = "Good afternoon";
  }

  const liveDate = now.toLocaleDateString([], {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const liveTime = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const stats = [
    { icon: "🔬", value: summary.total_analyses, label: "Total Analyses" },
    { icon: "🧬", value: summary.idc_detected, label: "IDC Detected" },
    { icon: "✅", value: summary.non_idc, label: "Non-IDC" },
    { icon: "📊", value: `${summary.avg_confidence}%`, label: "Avg Confidence" },
  ];

  const recentAnalyses = useMemo(() => {
    return summary.recent_analyses.map((item) => {
      const filename = item.image_path
        ? item.image_path.split("/").pop()
        : "Unknown file";

      const confidence = Number.isFinite(Number(item.confidence))
        ? Number(item.confidence) * 100
        : 0;

      const date = item.created_at
        ? new Date(item.created_at).toLocaleDateString()
        : "N/A";

      return {
        id: item.id,
        filename,
        result: item.prediction_label || "Unknown",
        confidence: Number(confidence.toFixed(2)),
        date,
      };
    });
  }, [summary.recent_analyses]);

  return (
    <div className="dashboard-page">
      <Navbar />

      <div className="dashboard-body">
        <div className="dash-header">
          <div>
            <h1>
              {greeting}, <span>{user.name}</span>
            </h1>
            <p>Here's your MedScan AI overview</p>
          </div>

          <div className="dash-date">
            <div>{liveDate}</div>
            <div>{liveTime}</div>
          </div>
        </div>

        {error && (
          <div className="empty-state" style={{ marginBottom: "1rem" }}>
            ⚠️ {error}
          </div>
        )}

        <div className="dash-stats">
          {stats.map((s) => (
            <div className="stat-card" key={s.label}>
              <div className="stat-icon">{s.icon}</div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="dash-recent">
          <h2>Recent Analyses</h2>

          {loading ? (
            <div className="empty-state">Loading recent analyses...</div>
          ) : recentAnalyses.length > 0 ? (
            <table className="recent-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Result</th>
                  <th>Confidence</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {recentAnalyses.map((row) => (
                  <tr key={row.id}>
                    <td>{row.filename}</td>
                    <td>
                      <span
                        className={`result-badge ${
                          row.result === "IDC" ? "idc" : "non-idc"
                        }`}
                      >
                        {row.result}
                      </span>
                    </td>
                    <td>
                      <div className="confidence-bar">
                        <div className="conf-track">
                          <div
                            className="conf-fill"
                            style={{ width: `${row.confidence}%` }}
                          />
                        </div>
                        {row.confidence}%
                      </div>
                    </td>
                    <td>{row.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              No analyses yet — start by uploading an image!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;