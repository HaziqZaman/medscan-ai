import { useEffect, useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import "./CaseHistory.css";

function CaseHistory() {
  const [filter, setFilter] = useState("All");
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const filters = ["All", "IDC", "Non-IDC"];

  useEffect(() => {
    const fetchCases = async () => {
      try {
        setLoading(true);
        setError("");

        const token = localStorage.getItem("token");

        if (!token) {
          throw new Error("You are not logged in. Please log in first.");
        }

        const res = await fetch("http://127.0.0.1:8000/cases", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.detail || "Failed to load case history");
        }

        setCases(data);
      } catch (err) {
        console.error(err);
        setError(err.message || "Failed to load case history");
      } finally {
        setLoading(false);
      }
    };

    fetchCases();
  }, []);

  const mappedCases = useMemo(() => {
    return cases.map((item) => {
      const rawConfidence = Number(item.confidence);
      const confidence =
        Number.isFinite(rawConfidence) ? rawConfidence * 100 : 0;

      const filename = item.image_path
        ? item.image_path.split("/").pop()
        : "Unknown file";

      const modelMap = {
        model_a: "Model A",
        model_b: "Model B",
        model_c: "Model C",
      };

      const formattedDate = item.created_at
        ? new Date(item.created_at).toLocaleString()
        : "N/A";

      return {
        id: item.id,
        filename,
        result: item.prediction_label || "Unknown",
        confidence: Number(confidence.toFixed(2)),
        model: modelMap[item.model_type] || item.model_type || "Unknown",
        date: formattedDate,
      };
    });
  }, [cases]);

  const filteredCases = useMemo(() => {
    return mappedCases.filter((item) =>
      filter === "All" ? true : item.result === filter
    );
  }, [mappedCases, filter]);

  return (
    <div className="history-page">
      <Navbar />

      <div className="history-body">
        <div className="history-header">
          <div>
            <h1>
              Case <span>History</span>
            </h1>
            <p>All previous AI analyses — educational records only</p>
          </div>

          <button className="history-clear-btn" disabled title="Not implemented yet">
            Clear All
          </button>
        </div>

        <div className="history-filters">
          {filters.map((f) => (
            <button
              key={f}
              className={`filter-btn ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="history-table-wrap">
          {loading ? (
            <div className="history-empty">
              <span>⏳</span>
              Loading case history...
            </div>
          ) : error ? (
            <div className="history-empty">
              <span>⚠️</span>
              {error}
            </div>
          ) : filteredCases.length > 0 ? (
            <table className="history-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Filename</th>
                  <th>Result</th>
                  <th>Confidence</th>
                  <th>Model</th>
                  <th>Date & Time</th>
                  <th>Case ID</th>
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((row, i) => (
                  <tr key={row.id}>
                    <td style={{ color: "rgba(243,245,244,0.25)" }}>{i + 1}</td>

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
                      <div className="conf-bar-row">
                        <div className="conf-track">
                          <div
                            className="conf-fill"
                            style={{ width: `${row.confidence}%` }}
                          />
                        </div>
                        {row.confidence}%
                      </div>
                    </td>

                    <td>{row.model}</td>

                    <td
                      style={{
                        color: "rgba(243,245,244,0.4)",
                        fontSize: "0.8rem",
                      }}
                    >
                      {row.date}
                    </td>

                    <td>
                      <span className="view-btn">#{row.id}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="history-empty">
              <span>📋</span>
              No cases found for this filter.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CaseHistory;