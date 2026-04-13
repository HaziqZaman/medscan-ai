import { useEffect, useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import toast from "react-hot-toast";
import "./CaseHistory.css";

const API_BASE = "http://127.0.0.1:8000";

const FILTERS = [
  { id: "All", label: "All" },
  { id: "model_a", label: "Model A" },
  { id: "model_b", label: "Model B" },
];

const MODEL_A_KEYS = ["note", "original_filename"];
const MODEL_B1_KEYS = [
  "nuclei_count",
  "avg_nuclei_area",
  "irregularity_score",
  "nuclei_density",
  "mask_positive_pixels",
  "coverage_ratio",
];
const MODEL_B2_KEYS = [
  "predicted_mitosis_count",
  "mitotic_activity",
  "mitotic_activity_level",
  "mask_positive_pixels",
  "coverage_ratio",
];

function parseExtraData(value) {
  if (!value) return {};
  if (typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      return {};
    }
  }
  return value;
}

function makeImageUrl(path) {
  if (!path) return null;
  const cleanPath = String(path).replace(/^\/+/, "").replace(/\\/g, "/");
  return `${API_BASE}/${cleanPath}`;
}

function formatLabel(key) {
  return key.replace(/_/g, " ");
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") {
    return Number.isInteger(value)
      ? String(value)
      : value.toFixed(4).replace(/\.?0+$/, "");
  }
  return String(value);
}

function getBadgeClass(result) {
  const value = String(result || "").toLowerCase();
  if (value === "idc") return "idc";
  if (value === "non-idc") return "non-idc";
  return "unknown";
}

function RenderDataRows({ data, allowedKeys }) {
  if (!data || typeof data !== "object") {
    return <div className="empty-mini">No details available.</div>;
  }

  const entries = (allowedKeys || Object.keys(data))
    .filter((key) => key in data)
    .map((key) => [key, data[key]]);

  if (!entries.length) {
    return <div className="empty-mini">No details available.</div>;
  }

  return (
    <div className="detail-list">
      {entries.map(([key, value]) => (
        <div key={key} className="detail-row">
          <span className="detail-key">{formatLabel(key)}</span>
          <span className="detail-val">{formatValue(value)}</span>
        </div>
      ))}
    </div>
  );
}

function ImageBlock({ title, src }) {
  return (
    <div className="panel">
      <h3 className="section-title">{title}</h3>
      {src ? (
        <img src={src} alt={title} className="modal-img" />
      ) : (
        <div className="empty-mini">Image not available.</div>
      )}
    </div>
  );
}

function CaseDetailModal({ row, onClose }) {
  if (!row) return null;

  const extra = row.extraData || {};
  const raw = row.raw || {};

  const originalImage = makeImageUrl(raw.image_path);

  const modelAOverlay = makeImageUrl(extra.overlay_path || raw.heatmap_path);
  const modelAHeatmap = makeImageUrl(extra.raw_heatmap_path);

  const b1Mask = makeImageUrl(extra?.b1_result?.mask_path);
  const b1Overlay = makeImageUrl(extra?.b1_result?.overlay_path);
  const b2Mask = makeImageUrl(extra?.b2_result?.mask_path);
  const b2Overlay = makeImageUrl(extra?.b2_result?.overlay_path);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">
              {row.model} — Case #{row.id}
            </h2>
            <p className="modal-subtitle">Saved on {row.date}</p>
          </div>
          <button onClick={onClose} className="close-btn">
            ✕
          </button>
        </div>

        <div className="summary-grid">
          <div className="summary-box">
            <div className="summary-label">Result</div>
            <div className="summary-value">{row.result}</div>
          </div>

          <div className="summary-box">
            <div className="summary-label">
              {row.modelType === "model_a" ? "Confidence" : "Assessment Type"}
            </div>
            <div className="summary-value">
              {row.modelType === "model_a"
                ? (row.confidence ? `${row.confidence}%` : "—")
                : "Feature-based interpretation"}
            </div>
          </div>

          <div className="summary-box">
            <div className="summary-label">Inference</div>
            <div className="summary-value">
              {raw.inference_time ? `${raw.inference_time}s` : "—"}
            </div>
          </div>

          <div className="summary-box">
            <div className="summary-label">Status</div>
            <div className="summary-value">{raw.result_status || "—"}</div>
          </div>
        </div>

        {row.modelType === "model_a" ? (
          <>
            <div className="panel-grid">
              <div className="panel">
                <h3 className="section-title">Model A Details</h3>
                <RenderDataRows data={extra} allowedKeys={MODEL_A_KEYS} />
              </div>
              <ImageBlock title="Input Image" src={originalImage} />
            </div>

            <div className="panel-grid" style={{ marginTop: "1.5rem" }}>
              <ImageBlock title="Overlay" src={modelAOverlay} />
              <ImageBlock title="Raw Heatmap" src={modelAHeatmap} />
            </div>
          </>
        ) : (
          <>
            <div className="panel-grid">
              <div className="panel">
                <h3 className="section-title">Combined Result</h3>
                <RenderDataRows
                  data={extra.combined_result || {}}
                  allowedKeys={["grade_support", "summary"]}
                />
                <div className="result-note" style={{ marginTop: "0.75rem" }}>
                  This result is based on fused nuclei and mitosis findings, not a direct probability score.
                </div>
              </div>
              <ImageBlock title="B1 Input Image" src={makeImageUrl(extra.b1_image_path)} />
            </div>

            <div className="panel-grid" style={{ marginTop: "1.5rem" }}>
              <div className="panel">
                <h3 className="section-title">B1 Findings</h3>
                <RenderDataRows
                  data={extra?.b1_result?.findings || {}}
                  allowedKeys={MODEL_B1_KEYS}
                />
              </div>
              <div className="panel">
                <h3 className="section-title">B2 Findings</h3>
                <RenderDataRows
                  data={extra?.b2_result?.findings || {}}
                  allowedKeys={MODEL_B2_KEYS}
                />
              </div>
            </div>

            <div className="panel-grid" style={{ marginTop: "1.5rem" }}>
              <ImageBlock title="B1 Mask" src={b1Mask} />
              <ImageBlock title="B1 Overlay" src={b1Overlay} />
            </div>

            <div className="panel-grid" style={{ marginTop: "1.5rem" }}>
              <ImageBlock title="B2 Mask" src={b2Mask} />
              <ImageBlock title="B2 Overlay" src={b2Overlay} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function CaseHistory() {
  const [filter, setFilter] = useState("All");
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState(null);

  const fetchCases = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");

      const res = await fetch(`${API_BASE}/cases`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to fetch case history");

      setCases(Array.isArray(data) ? data : []);
    } catch (err) {
      toast.error(err.message || "Failed to load case history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleDelete = async (id) => {
    const toastId = toast.loading("Deleting case...");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/cases/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Delete failed");

      setCases((prev) => prev.filter((c) => c.id !== id));

      if (selectedCase?.id === id) {
        setSelectedCase(null);
      }

      toast.success("Case deleted successfully", { id: toastId });
    } catch (err) {
      toast.error(err.message || "Delete failed", { id: toastId });
    }
  };

  const handleClearAll = async () => {
    const toastId = toast.loading("Clearing history...");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/cases/clear-all`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Clear all failed");

      setCases([]);
      setSelectedCase(null);

      toast.success("All history cleared", { id: toastId });
    } catch (err) {
      toast.error(err.message || "Clear all failed", { id: toastId });
    }
  };

  const mappedCases = useMemo(() => {
    return cases.map((item) => {
      const rawConfidence = Number(item.confidence);
      const dateObj = new Date(item.created_at);

      const formattedDate = isNaN(dateObj.getTime())
        ? "N/A"
        : dateObj.toLocaleString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          });

      return {
        id: item.id,
        filename: item.image_path?.split("/").pop() || "Unknown",
        result: item.prediction_label || "N/A",
        confidence:
          item.model_type === "model_a" && Number.isFinite(rawConfidence)
            ? (rawConfidence <= 1 ? rawConfidence * 100 : rawConfidence).toFixed(1)
            : null,
        assessmentType:
          item.model_type === "model_a"
            ? "Confidence-based"
            : "Feature-based interpretation",
        model: item.model_type === "model_a" ? "Model A" : "Model B",
        modelType: item.model_type,
        date: formattedDate,
        extraData: parseExtraData(item.extra_data),
        raw: item,
      };
    });
  }, [cases]);

  const filteredCases = mappedCases.filter(
    (c) => filter === "All" || c.modelType === filter
  );

  return (
    <div className="history-page">
      <Navbar />
      <div className="history-body">
        <div className="history-header">
          <h1>
            Case <span>History</span>
          </h1>
          <button
            className="history-clear-btn"
            onClick={handleClearAll}
            disabled={cases.length === 0}
          >
            Clear All History
          </button>
        </div>

        <div className="history-filters">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              className={`filter-btn ${filter === f.id ? "active" : ""}`}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="history-table-wrap">
          {loading ? (
            <div className="history-empty">Loading...</div>
          ) : filteredCases.length > 0 ? (
            <table className="history-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Filename</th>
                  <th>Result</th>
                  <th>Assessment</th>
                  <th>Model</th>
                  <th>Date & Time</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((row, i) => (
                  <tr key={row.id}>
                    <td>{i + 1}</td>
                    <td>{row.filename}</td>
                    <td>
                      <span className={`result-badge ${getBadgeClass(row.result)}`}>
                        {row.result}
                      </span>
                    </td>
                    <td>
                      {row.modelType === "model_a"
                        ? (row.confidence ? `${row.confidence}%` : "—")
                        : row.assessmentType}
                    </td>
                    <td>{row.model}</td>
                    <td className="date-cell">{row.date}</td>
                    <td className="actions-cell">
                      <button
                        className="action-btn view"
                        onClick={() => setSelectedCase(row)}
                        title="View Detail"
                      >
                        👁️
                      </button>
                      <button
                        className="action-btn delete"
                        onClick={() => handleDelete(row.id)}
                        title="Delete Case"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="history-empty">No records found.</div>
          )}
        </div>
      </div>

      <CaseDetailModal row={selectedCase} onClose={() => setSelectedCase(null)} />
    </div>
  );
}

export default CaseHistory;