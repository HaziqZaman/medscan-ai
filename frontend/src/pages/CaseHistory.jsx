import { useEffect, useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import "./CaseHistory.css";

const API_BASE = "http://127.0.0.1:8000";

const FILTERS = [
  { id: "All", label: "All" },
  { id: "model_a", label: "Model A" },
  { id: "model_b", label: "Model B" },
];

const MODEL_A_KEYS = ["note", "original_filename", "overlay_path", "raw_heatmap_path"];
const MODEL_B1_KEYS = [
  "submodel",
  "nuclei_count",
  "avg_nuclei_area",
  "irregularity_score",
  "nuclei_density",
  "mask_positive_pixels",
  "coverage_ratio",
];
const MODEL_B2_KEYS = [
  "submodel",
  "predicted_mitosis_count",
  "mitotic_activity",
  "mitotic_activity_level",
  "mask_positive_pixels",
  "coverage_ratio",
  "threshold",
  "min_component_area",
  "max_probability",
  "mean_probability",
];
const MODEL_B_COMBINED_KEYS = [
  "nuclei_count",
  "avg_nuclei_area",
  "irregularity_score",
  "nuclei_density",
  "predicted_mitosis_count",
  "mitotic_activity",
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

  if (Array.isArray(value)) {
    if (!value.length) return "0 items";
    const allPrimitive = value.every(
      (item) =>
        item === null ||
        ["string", "number", "boolean"].includes(typeof item)
    );
    return allPrimitive ? value.map(String).join(", ") : `${value.length} items`;
  }

  if (typeof value === "object") return null;

  return String(value);
}

function renderDataRows(data, allowedKeys = null) {
  if (!data || typeof data !== "object") {
    return <div style={emptyMiniStyle}>No details available.</div>;
  }

  const excluded = new Set(["objects", "source_image", "bbox", "centroid"]);
  const sourceKeys = allowedKeys || Object.keys(data);

  const entries = sourceKeys
    .filter((key) => key in data)
    .filter((key) => !excluded.has(key))
    .map((key) => [key, data[key]])
    .filter(([, value]) => formatValue(value) !== null);

  if (!entries.length) {
    return <div style={emptyMiniStyle}>No details available.</div>;
  }

  return (
    <div style={detailListStyle}>
      {entries.map(([key, value]) => (
        <div key={key} style={detailRowStyle}>
          <span style={detailKeyStyle}>{formatLabel(key)}</span>
          <span style={detailValueStyle}>{formatValue(value)}</span>
        </div>
      ))}
    </div>
  );
}

function getResultBadgeStyle(row) {
  const base = {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: "999px",
    padding: "6px 10px",
    fontSize: "0.76rem",
    fontWeight: 700,
    border: "1px solid transparent",
  };

  if (row.modelType === "model_a" && row.result === "IDC") {
    return {
      ...base,
      background: "#fff1f1",
      color: "#c83b3b",
      borderColor: "#f2c4c4",
    };
  }

  if (row.modelType === "model_a" && row.result === "Non-IDC") {
    return {
      ...base,
      background: "#edf9f2",
      color: "#159957",
      borderColor: "#cfe6d7",
    };
  }

  return {
    ...base,
    background: "#f4fbf7",
    color: "#156b49",
    borderColor: "#cfe6d7",
  };
}

function ImageCard({ title, src, alt }) {
  return (
    <div style={imageCardStyle}>
      <div style={sectionTitleStyle}>{title}</div>
      {src ? (
        <img
          src={src}
          alt={alt}
          style={{
            width: "100%",
            maxHeight: "280px",
            objectFit: "contain",
            display: "block",
            background: "#f8fbf9",
            borderRadius: "10px",
            border: "1px solid #e1eee7",
          }}
        />
      ) : (
        <div style={emptyMiniStyle}>Image not available</div>
      )}
    </div>
  );
}

function CaseDetailModal({ row, onClose }) {
  if (!row) return null;

  const extra = row.extraData || {};
  const originalImage = makeImageUrl(row.raw?.image_path);

  const modelAOverlay = makeImageUrl(extra.overlay_path || row.raw?.heatmap_path);
  const modelAHeatmap = makeImageUrl(extra.raw_heatmap_path);

  const b1 = extra.b1_result || {};
  const b2 = extra.b2_result || {};
  const combined = extra.combined_result || {};

  const b1Mask = makeImageUrl(b1.mask_path);
  const b1Overlay = makeImageUrl(b1.overlay_path);
  const b2Mask = makeImageUrl(b2.mask_path);
  const b2Overlay = makeImageUrl(b2.overlay_path);

  return (
    <div style={modalOverlayStyle} onClick={onClose}>
      <div style={modalCardStyle} onClick={(e) => e.stopPropagation()}>
        <div style={modalHeaderStyle}>
          <div>
            <div style={{ ...sectionTitleStyle, marginBottom: "0.45rem" }}>
              Case Detail
            </div>
            <h2 style={modalTitleStyle}>
              {row.model} — Case #{row.id}
            </h2>
            <p style={modalSubtitleStyle}>
              Saved on {row.date}
            </p>
          </div>

          <button onClick={onClose} style={closeBtnStyle}>
            ✕
          </button>
        </div>

        <div style={summaryGridStyle}>
          <div style={summaryBoxStyle}>
            <div style={summaryLabelStyle}>Result</div>
            <div style={summaryValueStyle}>{row.result}</div>
          </div>

          <div style={summaryBoxStyle}>
            <div style={summaryLabelStyle}>Model</div>
            <div style={summaryValueStyle}>{row.model}</div>
          </div>

          <div style={summaryBoxStyle}>
            <div style={summaryLabelStyle}>Confidence</div>
            <div style={summaryValueStyle}>
              {row.modelType === "model_a" && row.confidence !== null
                ? `${row.confidence}%`
                : "—"}
            </div>
          </div>

          <div style={summaryBoxStyle}>
            <div style={summaryLabelStyle}>Inference Time</div>
            <div style={summaryValueStyle}>
              {row.raw?.inference_time ? `${row.raw.inference_time}s` : "—"}
            </div>
          </div>
        </div>

        {row.modelType === "model_a" && (
          <>
            <div style={panelGridStyle}>
              <div style={panelStyle}>
                <div style={sectionTitleStyle}>Model A Details</div>
                {renderDataRows(extra, MODEL_A_KEYS)}
                {extra.note ? (
                  <div style={noteBoxStyle}>{extra.note}</div>
                ) : null}
                <div style={warningBoxStyle}>
                  Educational prediction only — not a clinical diagnosis.
                </div>
              </div>

              <ImageCard title="Uploaded Patch" src={originalImage} alt="Original uploaded patch" />
            </div>

            <div style={panelGridStyle}>
              <ImageCard title="Overlay" src={modelAOverlay} alt="Model A overlay" />
              <ImageCard title="Raw Heatmap" src={modelAHeatmap} alt="Model A raw heatmap" />
            </div>
          </>
        )}

        {row.modelType === "model_b" && (
          <>
            <div style={panelGridStyle}>
              <div style={panelStyle}>
                <div style={sectionTitleStyle}>B1 — Nuclei Analysis</div>
                {renderDataRows(b1.findings, MODEL_B1_KEYS)}
              </div>

              <div style={panelStyle}>
                <div style={sectionTitleStyle}>B2 — Mitosis Analysis</div>
                {renderDataRows(b2.findings, MODEL_B2_KEYS)}
              </div>
            </div>

            <div style={panelGridStyle}>
              <ImageCard title="B1 Mask" src={b1Mask} alt="B1 mask" />
              <ImageCard title="B1 Overlay" src={b1Overlay} alt="B1 overlay" />
            </div>

            <div style={panelGridStyle}>
              <ImageCard title="B2 Mask" src={b2Mask} alt="B2 mask" />
              <ImageCard title="B2 Overlay" src={b2Overlay} alt="B2 overlay" />
            </div>

            <div style={panelStyle}>
              <div style={sectionTitleStyle}>Combined Interpretation</div>
              <div style={summaryBoxStyle}>
                <div style={summaryLabelStyle}>Grade Support</div>
                <div style={summaryValueStyle}>
                  {combined.grade_support || row.result}
                </div>
              </div>

              {combined.summary ? (
                <div style={noteBoxStyle}>{combined.summary}</div>
              ) : null}

              {renderDataRows(combined.feature_summary, MODEL_B_COMBINED_KEYS)}

              <div style={warningBoxStyle}>
                Educational grading support only — not a definitive pathological grade.
              </div>
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
  const [error, setError] = useState("");
  const [selectedCase, setSelectedCase] = useState(null);

  useEffect(() => {
    const fetchCases = async () => {
      try {
        setLoading(true);
        setError("");

        const token = localStorage.getItem("token");
        if (!token) {
          throw new Error("You are not logged in. Please log in first.");
        }

        const res = await fetch(`${API_BASE}/cases`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.detail || "Failed to load case history");
        }

        setCases(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error(err);
        setError(err.message || "Failed to load case history");
      } finally {
        setLoading(false);
      }
    };

    fetchCases();
  }, []);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") setSelectedCase(null);
    };

    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, []);

  const mappedCases = useMemo(() => {
    return cases.map((item) => {
      const extraData = parseExtraData(item.extra_data);
      const rawConfidence = Number(item.confidence);
      const isModelA = item.model_type === "model_a";

      const confidence =
        isModelA && Number.isFinite(rawConfidence)
          ? Number((rawConfidence * 100).toFixed(2))
          : null;

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
        confidence,
        model: modelMap[item.model_type] || item.model_type || "Unknown",
        modelType: item.model_type,
        date: formattedDate,
        extraData,
        raw: item,
      };
    });
  }, [cases]);

  const filteredCases = useMemo(() => {
    return mappedCases.filter((item) => {
      if (filter === "All") return true;
      return item.modelType === filter;
    });
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
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((row, i) => (
                  <tr key={row.id}>
                    <td style={{ color: "rgba(243,245,244,0.25)" }}>{i + 1}</td>

                    <td>{row.filename}</td>

                    <td>
                      <span style={getResultBadgeStyle(row)}>
                        {row.result}
                      </span>
                    </td>

                    <td>
                      {row.confidence !== null ? (
                        <div className="conf-bar-row">
                          <div className="conf-track">
                            <div
                              className="conf-fill"
                              style={{ width: `${row.confidence}%` }}
                            />
                          </div>
                          {row.confidence}%
                        </div>
                      ) : (
                        <span style={{ color: "rgba(243,245,244,0.5)" }}>—</span>
                      )}
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
                      <button
                        className="view-btn"
                        onClick={() => setSelectedCase(row)}
                        style={{
                          cursor: "pointer",
                          border: "none",
                          background: "transparent",
                        }}
                        title={`View case #${row.id}`}
                      >
                        👁 View
                      </button>
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

      <CaseDetailModal row={selectedCase} onClose={() => setSelectedCase(null)} />
    </div>
  );
}

// ─── Inline modal styles so no extra CSS file is required ────────────────────
const modalOverlayStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(10, 22, 16, 0.55)",
  backdropFilter: "blur(4px)",
  zIndex: 9999,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "1.25rem",
};

const modalCardStyle = {
  width: "min(1100px, 100%)",
  maxHeight: "90vh",
  overflowY: "auto",
  background: "#ffffff",
  borderRadius: "18px",
  padding: "1.5rem",
  boxShadow: "0 20px 60px rgba(16, 38, 29, 0.22)",
  border: "1px solid #dcebe3",
};

const modalHeaderStyle = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: "1rem",
  marginBottom: "1.25rem",
};

const modalTitleStyle = {
  margin: 0,
  color: "#173428",
  fontSize: "1.45rem",
  fontWeight: 800,
  letterSpacing: "-0.4px",
};

const modalSubtitleStyle = {
  margin: "0.35rem 0 0",
  color: "#5f766b",
  fontSize: "0.9rem",
};

const closeBtnStyle = {
  width: "38px",
  height: "38px",
  borderRadius: "999px",
  border: "1px solid #dcebe3",
  background: "#f6fbf8",
  color: "#173428",
  cursor: "pointer",
  fontSize: "1rem",
  fontWeight: 700,
};

const summaryGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: "0.85rem",
  marginBottom: "1.25rem",
};

const summaryBoxStyle = {
  background: "#f7fbf8",
  border: "1px solid #e1eee7",
  borderRadius: "12px",
  padding: "0.9rem 1rem",
};

const summaryLabelStyle = {
  fontSize: "0.72rem",
  color: "#688175",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  marginBottom: "0.3rem",
};

const summaryValueStyle = {
  fontSize: "1rem",
  color: "#173428",
  fontWeight: 800,
};

const panelGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
  gap: "1rem",
  marginBottom: "1rem",
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #dcebe3",
  borderRadius: "14px",
  padding: "1rem",
  boxShadow: "0 8px 22px rgba(16, 38, 29, 0.05)",
};

const imageCardStyle = {
  background: "#ffffff",
  border: "1px solid #dcebe3",
  borderRadius: "14px",
  padding: "1rem",
  boxShadow: "0 8px 22px rgba(16, 38, 29, 0.05)",
};

const sectionTitleStyle = {
  fontSize: "0.78rem",
  fontWeight: 800,
  color: "#159957",
  letterSpacing: "0.8px",
  textTransform: "uppercase",
  marginBottom: "0.9rem",
};

const detailListStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.45rem",
};

const detailRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "1rem",
  padding: "0.55rem 0.8rem",
  background: "#f8fbf9",
  border: "1px solid #e1eee7",
  borderRadius: "8px",
};

const detailKeyStyle = {
  fontSize: "0.78rem",
  color: "#557064",
  fontWeight: 600,
  textTransform: "capitalize",
};

const detailValueStyle = {
  fontSize: "0.82rem",
  color: "#173428",
  fontWeight: 700,
  textAlign: "right",
};

const noteBoxStyle = {
  marginTop: "0.85rem",
  background: "#f7fbf8",
  border: "1px solid #e1eee7",
  borderRadius: "10px",
  padding: "0.8rem 0.95rem",
  color: "#3f584d",
  fontSize: "0.84rem",
  lineHeight: 1.6,
};

const warningBoxStyle = {
  marginTop: "0.85rem",
  background: "#fff9e8",
  border: "1px solid #f2e0ad",
  borderRadius: "10px",
  padding: "0.8rem 0.95rem",
  color: "#8a650f",
  fontSize: "0.84rem",
  lineHeight: 1.6,
};

const emptyMiniStyle = {
  background: "#f8fbf9",
  border: "1px dashed #dcebe3",
  borderRadius: "10px",
  padding: "0.9rem",
  color: "#5f766b",
  fontSize: "0.82rem",
};

export default CaseHistory;