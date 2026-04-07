import { useState, useRef } from "react";
import Navbar from "../components/Navbar";
import "./Analysis.css";

// ─── Helpers ──────────────────────────────────────────────────────────────────
const B1_DISPLAY_KEYS = [
  "submodel",
  "nuclei_count",
  "avg_nuclei_area",
  "irregularity_score",
  "nuclei_density",
  "mask_positive_pixels",
  "coverage_ratio",
];

const B2_DISPLAY_KEYS = [
  "submodel",
  "predicted_mitosis_count",
  "mitotic_activity",
  "mitotic_activity_level",
  "mask_positive_pixels",
  "coverage_ratio",
  "threshold",
  "min_component_area",
];

const FEATURE_SUMMARY_KEYS = [
  "nuclei_count",
  "avg_nuclei_area",
  "irregularity_score",
  "nuclei_density",
  "predicted_mitosis_count",
  "mitotic_activity",
];

function formatLabel(key) {
  return key.replace(/_/g, " ");
}

function formatValue(val) {
  if (val === null || val === undefined || val === "") return "—";
  if (typeof val === "number") {
    return Number.isInteger(val) ? String(val) : val.toFixed(4).replace(/\.?0+$/, "");
  }
  if (Array.isArray(val)) {
    if (val.length === 0) return "0 items";
    const allPrimitive = val.every(
      (item) =>
        item === null ||
        ["string", "number", "boolean"].includes(typeof item)
    );
    return allPrimitive ? val.map(String).join(", ") : `${val.length} items`;
  }
  if (typeof val === "object") {
    return null;
  }
  return String(val);
}

// ─── Model Switcher ───────────────────────────────────────────────────────────
function ModelSwitcher({ active, onChange }) {
  const models = [
    { id: "model_a", label: "Model A", sub: "IDC Detection" },
    { id: "model_b", label: "Model B", sub: "Grading Support" },
    { id: "model_c", label: "Model C", sub: "Lymph Node", disabled: false, soon: true },
  ];

  return (
    <div className="model-switcher">
      {models.map((m) => (
        <button
          key={m.id}
          className={`model-tab ${active === m.id ? "active" : ""} ${m.disabled ? "disabled" : ""}`}
          onClick={() => !m.disabled && onChange(m.id)}
          disabled={m.disabled}
        >
          <span className="tab-label">{m.label}</span>
          <span className="tab-sub">{m.sub}</span>
          {m.soon && <span className="tab-badge">Soon</span>}
        </button>
      ))}
    </div>
  );
}

// ─── Upload Card ──────────────────────────────────────────────────────────────
function UploadCard({ label, hint, file, preview, onFile }) {
  const fileRef = useRef();
  const [dragover, setDragover] = useState(false);

  const handleFile = (f) => {
    if (!f) return;
    const reader = new FileReader();
    reader.onload = (e) => onFile(f, e.target.result);
    reader.readAsDataURL(f);
  };

  return (
    <div className="upload-card">
      {label && <div className="upload-card-label">{label}</div>}
      <div
        className={`upload-zone ${dragover ? "dragover" : ""}`}
        onClick={() => fileRef.current.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragover(true);
        }}
        onDragLeave={() => setDragover(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragover(false);
          handleFile(e.dataTransfer.files[0]);
        }}
      >
        <div className="upload-icon">🔬</div>
        <p>
          <span>Click to upload</span> or drag & drop
          <br />
          {hint}
        </p>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="upload-input"
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {preview && (
        <div className="uploaded-preview">
          <img src={preview} alt="Preview" />
          <div className="upload-filename">{file?.name}</div>
        </div>
      )}
    </div>
  );
}

// ─── Result Card ──────────────────────────────────────────────────────────────
function ResultCard({ title, children }) {
  return (
    <div className="result-card">
      <div className="result-section-title">{title}</div>
      {children}
    </div>
  );
}

// ─── Findings Renderer ───────────────────────────────────────────────────────
function renderFindings(findings, allowedKeys = null) {
  if (!findings) return null;

  if (typeof findings === "string") {
    return <div className="result-note">{findings}</div>;
  }

  if (Array.isArray(findings)) {
    return (
      <ul className="findings-list">
        {findings.map((item, i) => (
          <li key={i}>{String(item)}</li>
        ))}
      </ul>
    );
  }

  if (typeof findings === "object") {
    const excludedKeys = new Set([
      "objects",
      "source_image",
      "bbox",
      "centroid",
    ]);

    const entries = (allowedKeys || Object.keys(findings))
      .filter((key) => key in findings)
      .filter((key) => !excludedKeys.has(key))
      .map((key) => [key, findings[key]])
      .filter(([, val]) => formatValue(val) !== null);

    if (!entries.length) {
      return <div className="result-note">No structured findings available.</div>;
    }

    return (
      <div className="findings-table">
        {entries.map(([key, val]) => (
          <div className="findings-row" key={key}>
            <span className="findings-key">{formatLabel(key)}</span>
            <span className="findings-val">{formatValue(val)}</span>
          </div>
        ))}
      </div>
    );
  }

  return <div className="result-note">{String(findings)}</div>;
}

// ─── Model A Section ──────────────────────────────────────────────────────────
function ModelASection() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFile = (f, dataUrl) => {
    setFile(f);
    setPreview(dataUrl);
    setResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setLoadingStage("Uploading image...");
    setResult(null);
    setError(null);

    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("You are not logged in. Please log in first.");

      const formData = new FormData();
      formData.append("file", file);

      setTimeout(() => setLoadingStage("Processing image..."), 600);
      setTimeout(() => setLoadingStage("Running Model A..."), 1200);

      const res = await fetch("http://127.0.0.1:8000/analysis/predict", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");

      setResult({
        case_id: data.case_id,
        prediction: data.prediction,
        confidence: Number(data.confidence) * 100,
        model: data.model,
        note: data.note,
        inference_time: data.inference_time,
        overlay: data.overlay,
        heatmap: data.heatmap,
      });
    } catch (err) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
      setLoadingStage("");
    }
  };

  const safeConf = Number.isFinite(result?.confidence) ? result.confidence : 0;

  return (
    <div className="analysis-panel">
      <div className="upload-grid single">
        <UploadCard
          hint="50×50 histopathology patch (PNG, JPG)"
          file={file}
          preview={preview}
          onFile={handleFile}
        />
      </div>

      <div className="patch-note">
        ⚠️ Only 50×50 px histopathology patches are accepted for Model A.
      </div>

      {error && <div className="error-message">{error}</div>}

      <button className="analyze-btn" onClick={handleAnalyze} disabled={!file || loading}>
        {loading ? (
          <>
            <span className="btn-spinner" /> {loadingStage || "Analyzing Model A..."}
          </>
        ) : (
          "Analyze with Model A"
        )}
      </button>

      {loading && (
        <div className="loading-state">
          <div className="spinner" />
          <span>{loadingStage}</span>
        </div>
      )}

      {result && !loading && (
        <div className="result-grid">
          <ResultCard title="Prediction">
            <div className="result-main">
              <div>
                <div className="result-label">Classification</div>
                <div className={`result-value ${result.prediction === "IDC" ? "idc" : "non-idc"}`}>
                  {result.prediction}
                </div>
              </div>
              <div className="result-conf">
                <div className="result-label">Confidence</div>
                <div className="conf-value">{safeConf.toFixed(2)}%</div>
              </div>
            </div>

            <div className="conf-bar-full">
              <div className="conf-bar-fill" style={{ width: `${safeConf}%` }} />
            </div>

            <div className="result-meta-row">
              <span>Model: {result.model}</span>
              <span>Inference: {result.inference_time}s</span>
              {result.case_id && <span>Case ID: {result.case_id}</span>}
            </div>

            {result.note && <div className="result-note">{result.note}</div>}
            <div className="result-note edu-note">
              ⚠️ Educational prediction only — not a clinical diagnosis.
            </div>
          </ResultCard>

          <ResultCard title="Uploaded Patch">
            <div className="image-preview">
              <img src={preview} alt="Uploaded patch" />
            </div>
          </ResultCard>

          <ResultCard title="Grad-CAM Visualization">
            {result.overlay && result.prediction === "IDC" ? (
              <div className="image-preview">
                <img
                  src={`data:image/png;base64,${result.overlay}`}
                  alt="Grad-CAM heatmap"
                />
                <div className="result-note" style={{ marginTop: "0.75rem" }}>
                  Highlighted regions show areas most influential in the IDC prediction.
                </div>
              </div>
            ) : (
              <div className="heatmap-placeholder">
                <span>🗺️</span>
                {result.prediction === "IDC"
                  ? "No heatmap returned"
                  : "Visualization only shown for IDC-positive predictions"}
              </div>
            )}
          </ResultCard>
        </div>
      )}
    </div>
  );
}

// ─── Model B Section ──────────────────────────────────────────────────────────
function ModelBSection() {
  const [b1File, setB1File] = useState(null);
  const [b1Preview, setB1Preview] = useState(null);
  const [b2File, setB2File] = useState(null);
  const [b2Preview, setB2Preview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!b1File || !b2File) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("You are not logged in. Please log in first.");

      const formData = new FormData();
      formData.append("b1_image", b1File);
      formData.append("b2_image", b2File);

      const res = await fetch("http://127.0.0.1:8000/analysis/predict/model-b", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Model B analysis failed");

      setResult(data);
    } catch (err) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-panel">
      <div className="model-b-hint">
        Both images are required. B1 captures nuclei structure (NuSeC), B2 captures
        mitosis patterns (MiDeSeC).
      </div>

      <div className="upload-grid double">
        <UploadCard
          label="B1 Image — NuSeC (Nuclei Analysis)"
          hint="Nuclei segmentation patch (PNG, JPG)"
          file={b1File}
          preview={b1Preview}
          onFile={(f, url) => {
            setB1File(f);
            setB1Preview(url);
            setResult(null);
            setError(null);
          }}
        />
        <UploadCard
          label="B2 Image — MiDeSeC (Mitosis Analysis)"
          hint="Mitosis detection patch (PNG, JPG)"
          file={b2File}
          preview={b2Preview}
          onFile={(f, url) => {
            setB2File(f);
            setB2Preview(url);
            setResult(null);
            setError(null);
          }}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <button
        className="analyze-btn"
        onClick={handleAnalyze}
        disabled={!b1File || !b2File || loading}
      >
        {loading ? (
          <>
            <span className="btn-spinner" /> Analyzing Model B...
          </>
        ) : (
          "Analyze with Model B"
        )}
      </button>

      {loading && (
        <div className="loading-state">
          <div className="spinner" />
          <span>Running grading analysis...</span>
        </div>
      )}

      {result && !loading && (
        <div className="result-grid">
          <ResultCard title="B1 — Nuclei Result">
            {renderFindings(result.b1_result?.findings, B1_DISPLAY_KEYS)}
            {result.b1_result?.mask && (
              <div className="image-preview" style={{ marginTop: "0.75rem" }}>
                <div className="result-label">Mask</div>
                <img src={`data:image/png;base64,${result.b1_result.mask}`} alt="B1 Mask" />
              </div>
            )}
            {result.b1_result?.overlay && (
              <div className="image-preview" style={{ marginTop: "0.75rem" }}>
                <div className="result-label">Overlay</div>
                <img src={`data:image/png;base64,${result.b1_result.overlay}`} alt="B1 Overlay" />
              </div>
            )}
          </ResultCard>

          <ResultCard title="B2 — Mitosis Result">
            {renderFindings(result.b2_result?.findings, B2_DISPLAY_KEYS)}
            {result.b2_result?.mask && (
              <div className="image-preview" style={{ marginTop: "0.75rem" }}>
                <div className="result-label">Mask</div>
                <img src={`data:image/png;base64,${result.b2_result.mask}`} alt="B2 Mask" />
              </div>
            )}
            {result.b2_result?.overlay && (
              <div className="image-preview" style={{ marginTop: "0.75rem" }}>
                <div className="result-label">Overlay</div>
                <img src={`data:image/png;base64,${result.b2_result.overlay}`} alt="B2 Overlay" />
              </div>
            )}
          </ResultCard>

          <div className="combined-result-card">
            <div className="result-section-title">Combined Interpretation</div>

            {result.case_id || result.inference_time ? (
              <div className="result-meta-row" style={{ marginBottom: "0.9rem" }}>
                {result.case_id && <span>Case ID: {result.case_id}</span>}
                {result.inference_time && <span>Inference: {result.inference_time}s</span>}
              </div>
            ) : null}

            {result.combined_result?.grade_support && (
              <div className="combined-row">
                <div className="result-label">Grade Support</div>
                <div className="combined-value">{String(result.combined_result.grade_support)}</div>
              </div>
            )}

            {result.combined_result?.summary && (
              <div className="result-note" style={{ marginTop: "0.75rem" }}>
                {String(result.combined_result.summary)}
              </div>
            )}

            {result.combined_result?.feature_summary && (
              <div style={{ marginTop: "0.5rem" }}>
                {renderFindings(result.combined_result.feature_summary, FEATURE_SUMMARY_KEYS)}
              </div>
            )}

            <div className="result-note edu-note" style={{ marginTop: "0.75rem" }}>
              ⚠️ Educational prediction only — not a clinical diagnosis.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Model C Section ──────────────────────────────────────────────────────────
function ModelCSection() {
  return (
    <div className="analysis-panel">
      <div className="model-c-card">
        <div className="coming-soon-icon">🧬</div>
        <div className="coming-soon-title">Coming Soon</div>
        <div className="coming-soon-text">
          Model C integration is planned for the final phase.
          <br />
          It will support lymph node metastasis detection using the PatchCamelyon (PCam) dataset.
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
function Analysis() {
  const [activeModel, setActiveModel] = useState("model_a");

  return (
    <div className="analysis-page">
      <Navbar />

      <div className="analysis-body">
        <div className="analysis-header">
          <div className="edu-badge">Educational Tool</div>
          <h1>
            Image <span>Analysis</span>
          </h1>
          <p>Select a model and upload the required image(s) for educational analysis.</p>
        </div>

        <ModelSwitcher active={activeModel} onChange={setActiveModel} />

        {activeModel === "model_a" && <ModelASection />}
        {activeModel === "model_b" && <ModelBSection />}
        {activeModel === "model_c" && <ModelCSection />}
      </div>
    </div>
  );
}

export default Analysis;