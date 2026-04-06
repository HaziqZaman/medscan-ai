import { useState, useRef } from "react";
import Navbar from "../components/Navbar";
import "./Analysis.css";

function Analysis() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [result, setResult] = useState(null);
  const [dragover, setDragover] = useState(false);
  const fileRef = useRef();

  const handleFile = (file) => {
    if (!file) return;

    setImage(file);
    setResult(null);

    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragover(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleAnalyze = async () => {
    if (!image) return;

    setLoading(true);
    setLoadingStage("Uploading image...");
    setResult(null);

    try {
      const token = localStorage.getItem("token");

      if (!token) {
        throw new Error("You are not logged in. Please log in first.");
      }

      const formData = new FormData();
      formData.append("file", image);

      const responsePromise = fetch("http://127.0.0.1:8000/analysis/predict", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      setTimeout(() => setLoadingStage("Processing image..."), 600);
      setTimeout(() => setLoadingStage("Running AI model..."), 1200);

      const res = await responsePromise;
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Analysis failed");
      }

      setResult({
        case_id: data.case_id,
        prediction: data.prediction,
        confidence: Number(data.confidence) * 100,
        model: data.model,
        note: data.note,
        inference_time: data.inference_time,
        overlay: data.overlay,
        heatmap: data.heatmap,
        image_path: data.image_path,
        overlay_path: data.overlay_path,
        raw_heatmap_path: data.raw_heatmap_path,
      });
    } catch (error) {
      console.error(error);
      alert(error.message || "Analysis failed");
    } finally {
      setLoading(false);
      setLoadingStage("");
    }
  };

  const safeConfidence = Number.isFinite(result?.confidence)
    ? result.confidence
    : 0;

  return (
    <div className="analysis-page">
      <Navbar />

      <div className="analysis-body">
        <div className="analysis-header">
          <div className="edu-badge">Educational Tool</div>
          <h1>
            Image <span>Analysis</span>
          </h1>
          <p>
            Upload a 50×50 histopathology patch to get AI prediction and model
            focus visualization
          </p>
        </div>

        <div className="analysis-grid">
          <div className="analysis-card">
            <h2>Upload Image Patch</h2>

            <div
              className={`upload-zone ${dragover ? "dragover" : ""}`}
              onClick={() => fileRef.current.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragover(true);
              }}
              onDragLeave={() => setDragover(false)}
              onDrop={handleDrop}
            >
              <div className="upload-icon">🔬</div>
              <p>
                <span>Click to upload</span> or drag & drop
                <br />
                50×50 histopathology patch (PNG, JPG)
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
                <img src={preview} alt="Uploaded patch" />
                <div className="upload-filename">{image?.name}</div>
              </div>
            )}

            <button
              className="analyze-btn"
              onClick={handleAnalyze}
              disabled={!image || loading}
            >
              {loading ? "Analyzing..." : "Run AI Analysis"}
            </button>
          </div>

          <div className="analysis-card">
            <h2>Prediction Result</h2>

            {loading ? (
              <div className="loading-spinner">
                <div className="spinner" />
                <p>{loadingStage}</p>
              </div>
            ) : result ? (
              <div className="result-content">
                <div className="result-main">
                  <div>
                    <div className="result-label">Prediction</div>
                    <div
                      className={`result-value ${
                        result.prediction === "IDC" ? "idc" : "non-idc"
                      }`}
                    >
                      {result.prediction}
                    </div>
                  </div>

                  <div className="result-conf">
                    <div className="result-label">Confidence</div>
                    <div className="conf-value">
                      {safeConfidence.toFixed(2)}%
                    </div>
                  </div>
                </div>

                <div className="conf-bar-full">
                  <div
                    className="conf-bar-fill"
                    style={{ width: `${safeConfidence}%` }}
                  />
                </div>

                <div className="result-label" style={{ marginTop: "0.25rem" }}>
                  Model: {result.model}
                </div>
                <div className="result-label">
                  Inference Time: {result.inference_time} s
                </div>

                {result.case_id && (
                  <div className="result-label">Case ID: {result.case_id}</div>
                )}

                {result.note && <div className="result-note">{result.note}</div>}

                <div className="result-note">
                  ⚠️ This is an educational prediction only. Not a clinical
                  diagnosis.
                </div>
              </div>
            ) : (
              <div className="result-placeholder">
                <span>📊</span>
                Upload an image and run analysis to see results here
              </div>
            )}
          </div>

          <div className="analysis-card">
            <h2>Model Focus Visualization</h2>

            {loading ? (
              <div className="heatmap-placeholder">
                <span>🗺️</span>
                Generating visualization...
              </div>
            ) : result?.overlay && result?.prediction === "IDC" ? (
              <div className="heatmap-content">
                <img
                  src={`data:image/png;base64,${result.overlay}`}
                  alt="Model Focus Visualization"
                  className="heatmap-image"
                />
                <div className="result-note" style={{ marginTop: "0.75rem" }}>
                  Highlighted regions show tissue areas most influential in the
                  IDC prediction.
                </div>
              </div>
            ) : result ? (
              <div className="heatmap-placeholder">
                <span>🗺️</span>
                No visualization shown for Non-IDC prediction
              </div>
            ) : (
              <div className="heatmap-placeholder">
                <span>🗺️</span>
                Visualization will appear here after analysis
              </div>
            )}
          </div>

          <div className="analysis-card">
            <h2>About This Model</h2>
            <div className="info-pills">
              {[
                "ResNet-18 Architecture",
                "Transfer Learning",
                "IDC Dataset — Kaggle",
                "50,000 Image Subset",
                "Recall: 0.80",
                "PyTorch",
                "Grad-CAM Ready",
                "50×50 px input",
              ].map((tag) => (
                <div className="info-pill" key={tag}>
                  {tag}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Analysis;