import { useState, useEffect, useRef } from "react";
import Navbar from "../components/Navbar";
import "./About.css";

/* ══════════════════════════════════════════════════
   DATA
══════════════════════════════════════════════════ */

const STATS = [
  { value: 3,     suffix: "",  label: "CNN Models",       icon: "🤖" },
  { value: 7,     suffix: "",  label: "UI Modules",       icon: "🖥️" },
  { value: 2,     suffix: "",  label: "LLM Providers",    icon: "✨" },
];

const ARCH_TREE = {
  id: "root", icon: "🏥", label: "MedScan AI", desc: "Complete Educational Platform", color: "green", open: true,
  children: [
    {
      id: "frontend", icon: "⚛️", label: "Frontend Layer", desc: "React + Vite SPA", color: "blue", open: true,
      children: [
        { id: "pages",  icon: "📄", label: "7 UI Pages",       desc: "Dashboard · Analysis · History · Chat · Knowledge…", leaf: true },
        { id: "css",    icon: "🎨", label: "Custom CSS",        desc: "Component-level styling with CSS variables",            leaf: true },
        { id: "authcl", icon: "🔐", label: "JWT Client",        desc: "Token-based auth flow",                                 leaf: true },
        { id: "toast",  icon: "🔔", label: "react-hot-toast",   desc: "In-app notifications",                                  leaf: true },
      ],
    },
    {
      id: "backend", icon: "⚡", label: "Backend Layer", desc: "FastAPI + SQLite", color: "amber", open: true,
      children: [
        { id: "routers",  icon: "🔀", label: "Modular Routers",   desc: "auth · analysis · chatbot · cases · dashboard",   leaf: true },
        { id: "schemas",  icon: "📋", label: "Pydantic Schemas",   desc: "Strict input/output validation",                   leaf: true },
        { id: "orm",      icon: "🗄️", label: "SQLAlchemy ORM",    desc: "Users · Cases · ChatSessions · Messages",           leaf: true },
        { id: "imgproc",  icon: "🖼️", label: "Image Processor",   desc: "OpenCV + Base64 + UUID file storage",               leaf: true },
      ],
    },
    {
      id: "ml", icon: "🤖", label: "ML Layer", desc: "PyTorch CNN Models", color: "purple", open: false,
      children: [
        {
          id: "modela", icon: "🔬", label: "Model A — IDC Detection", desc: "ResNet-18 classifier", open: false,
          children: [
            { id: "a1", icon: "📦", label: "Kaggle IDC Dataset", desc: "~50k histopathology patches", leaf: true },
            { id: "a2", icon: "🗺️", label: "Grad-CAM XAI",      desc: "Visual explainability heatmaps", leaf: true },
          ],
        },
        {
          id: "modelb1", icon: "🧬", label: "Model B1 — Nuclei Analysis", desc: "U-Net segmentation", open: false,
          children: [
            { id: "b11", icon: "📊", label: "NuSeC Dataset",  desc: "Nuclei density & morphology features", leaf: true },
            { id: "b12", icon: "🎭", label: "Seg Masks",       desc: "Overlay visualizations",               leaf: true },
          ],
        },
        {
          id: "modelb2", icon: "🔴", label: "Model B2 — Mitosis Detection", desc: "CNN activity estimator", open: false,
          children: [
            { id: "b21", icon: "📊", label: "MiDeSeC Dataset", desc: "Mitosis activity level data",        leaf: true },
            { id: "b22", icon: "🎯", label: "Grade Support",   desc: "Combined B1+B2 interpretation output", leaf: true },
          ],
        },
      ],
    },
    {
      id: "rag", icon: "💬", label: "RAG Chatbot", desc: "Hybrid LLM pipeline", color: "teal", open: false,
      children: [
        { id: "r1", icon: "🔍", label: "BM25 Search",           desc: "Lexical retrieval layer",                   leaf: true },
        { id: "r2", icon: "🧮", label: "Vector Search",         desc: "MiniLM dense semantic embeddings",           leaf: true },
        { id: "r3", icon: "⚖️", label: "Reranker",              desc: "Cross-encoder relevance scoring",            leaf: true },
        { id: "r4", icon: "✨", label: "Gemini (Primary LLM)",  desc: "Google Gemini generation layer",             leaf: true },
        { id: "r5", icon: "🔄", label: "DeepSeek (Fallback)",   desc: "Robust backup LLM",                          leaf: true },
        { id: "r6", icon: "🛡️", label: "Grounded Fallback",    desc: "Local response if both LLMs fail",           leaf: true },
      ],
    },
  ],
};

const STACK_TABS = ["All", "Frontend", "Backend", "ML", "Data"];
const STACK = [
  { icon: "⚛️", label: "Frontend",     name: "React + Vite",  tab: "Frontend", desc: "Modern SPA with Vite bundler" },
  { icon: "⚡", label: "API Layer",    name: "FastAPI",        tab: "Backend",  desc: "High-performance Python API" },
  { icon: "🔐", label: "Auth",         name: "JWT Auth",       tab: "Backend",  desc: "Token-based secure auth" },
  { icon: "🗄️", label: "Database",    name: "SQLite",         tab: "Backend",  desc: "Lightweight relational store" },
  { icon: "🔥", label: "ML Framework", name: "PyTorch",        tab: "ML",       desc: "Deep learning backbone" },
  { icon: "🧠", label: "Classifier",   name: "ResNet-18",      tab: "ML",       desc: "IDC detection CNN model" },
  { icon: "🗺️", label: "XAI",         name: "Grad-CAM",       tab: "ML",       desc: "Visual explainability layer" },
  { icon: "🔬", label: "Segmentation", name: "U-Net",          tab: "ML",       desc: "Nuclei segmentation model" },
  { icon: "📦", label: "IDC Dataset",  name: "Kaggle IDC",     tab: "Data",     desc: "Model A training data" },
  { icon: "🧬", label: "Nuclei",       name: "NuSeC",          tab: "Data",     desc: "Model B1 training data" },
  { icon: "🔴", label: "Mitosis",      name: "MiDeSeC",        tab: "Data",     desc: "Model B2 training data" },
  { icon: "📝", label: "Embeddings",   name: "MiniLM",         tab: "ML",       desc: "Sentence transformer model" },
];

const TEAM = [
  {
    name: "Haziq Zaman Chaudhry",
    role: "Full Stack Developer",
    avatar: "🧑‍💻",
    color: "var(--primary)",
    colorHex: "#17c964",
    tasks: ["System Architecture", "FastAPI Backend", "React Frontend", "DB Design", "Documentation"],
    detail: "Designed the full system from scratch — FastAPI backend with modular routers, React+Vite frontend, SQLite schema, JWT auth, case history, dashboard analytics, and complete API integration.",
    github: "HaziqZaman",
  },
  {
    name: "Sami Khan",
    role: "Frontend & ML Engineer",
    avatar: "👨‍🔬",
    color: "#006FEE",
    colorHex: "#006FEE",
    tasks: ["CNN Model Training", "Dataset Processing", "Grad-CAM Pipeline", "UI Components", "Model B Pipeline"],
    detail: "Trained and fine-tuned the CNN models (ResNet-18, U-Net), built the Grad-CAM visual explainability pipeline, processed all three datasets, and developed key frontend components.",
    github: "SamiBoxer",
  },
];

const PIPELINE_STEPS = [
  { icon: "💬", label: "User Query",   color: "#17c964", note: "A student asks a histopathology question" },
  { icon: "🔍", label: "BM25",         color: "#006FEE", note: "Lexical keyword search over the knowledge base" },
  { icon: "🧮", label: "Vector",       color: "#7828C8", note: "MiniLM dense semantic vector retrieval" },
  { icon: "⚖️", label: "Rerank",       color: "#F5A524", note: "Cross-encoder scores & sorts the best chunks" },
  { icon: "✨", label: "Gemini",       color: "#17c964", note: "Primary LLM generates a grounded answer" },
  { icon: "🔄", label: "DeepSeek",    color: "#F31260", note: "Fallback LLM if Gemini is unavailable" },
  { icon: "📤", label: "Response",    color: "#17c964", note: "Educational answer delivered to the student ✅" },
];

const FUN_FACTS = [
  "The RAG chatbot has 3 fallback layers — it never gives up 💪",
  "Grad-CAM shows exactly where the AI is 'looking' in a slide 👁️",
  "Entire system built by just 2 CS students in one semester 🚀",
  "ResNet-18 chosen for its clean Grad-CAM integration 🗺️",
  "100% public datasets — no real patient data ever used 🔒",
];

/* ══════════════════════════════════════════════════
   HOOKS
══════════════════════════════════════════════════ */
function useInView(threshold = 0.15) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setInView(true); },
      { threshold }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return [ref, inView];
}

function useCountUp(target, duration = 1600, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let t0 = null;
    const tick = (ts) => {
      if (!t0) t0 = ts;
      const p = Math.min((ts - t0) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setCount(Math.floor(eased * target));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [start, target, duration]);
  return count;
}

/* ══════════════════════════════════════════════════
   TREE NODE
══════════════════════════════════════════════════ */
function TreeNode({ node, depth = 0 }) {
  const [open, setOpen] = useState(node.open ?? false);
  const hasChildren = !!(node.children && node.children.length);
  const colorMap = { green: "#17c964", blue: "#006FEE", amber: "#F5A524", purple: "#7828C8", teal: "#17c964" };
  const accent = colorMap[node.color] || "var(--border)";

  return (
    <div className={`tn tn-d${depth}`} style={{ "--na": accent }}>
      <div
        className={`tn-row ${hasChildren ? "tn-row--btn" : ""} ${node.leaf ? "tn-row--leaf" : ""}`}
        style={{ paddingLeft: `${depth * 1.5 + 0.85}rem` }}
        onClick={() => hasChildren && setOpen(o => !o)}
      >
        <span className={`tn-caret ${hasChildren ? "" : "tn-caret--hidden"} ${open ? "tn-caret--open" : ""}`}>▶</span>
        <span className="tn-ico">{node.icon}</span>
        <span className="tn-lbl">{node.label}</span>
        {node.desc && <span className="tn-desc">{node.desc}</span>}
        {node.color && !node.leaf && (
          <span className="tn-chip" style={{ background: `${accent}18`, color: accent, border: `1px solid ${accent}33` }}>
            {node.color}
          </span>
        )}
      </div>
      {hasChildren && open && (
        <div className="tn-children">
          {node.children.map(c => <TreeNode key={c.id} node={c} depth={depth + 1} />)}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════
   SUB-COMPONENTS
══════════════════════════════════════════════════ */
function StatCard({ icon, value, suffix, label, delay, started }) {
  const count = useCountUp(value, 1500, started);
  return (
    <div className="stat-card" style={{ animationDelay: `${delay}ms` }}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-value">{value >= 1000 ? count.toLocaleString() : count}{suffix}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function TeamCard({ member }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <div className="team-flip-wrap" onClick={() => setFlipped(f => !f)}>
      <div className={`team-flip-inner ${flipped ? "flipped" : ""}`}>
        <div className="team-face team-front">
          <div className="team-glow-top" style={{ background: `radial-gradient(circle, ${member.colorHex}18 0%, transparent 70%)` }} />
          <div className="team-avatar-ring" style={{ borderColor: member.colorHex }}>{member.avatar}</div>
          <div className="team-name">{member.name}</div>
          <div className="team-role" style={{ color: member.colorHex }}>{member.role}</div>
          <div className="team-pills">{member.tasks.map(t => <span key={t} className="team-pill">{t}</span>)}</div>
          <span className="flip-cue">Click to flip ↩</span>
        </div>
        <div className="team-face team-back" style={{ borderColor: member.colorHex }}>
          <div className="team-glow-top" style={{ background: `radial-gradient(circle, ${member.colorHex}18 0%, transparent 70%)` }} />
          <div style={{ fontSize: "2.2rem", marginBottom: "0.4rem" }}>{member.avatar}</div>
          <div className="team-name">{member.name}</div>
          <p className="team-back-desc">{member.detail}</p>
          <a className="team-gh-link" href={`https://github.com/${member.github}`}
            target="_blank" rel="noreferrer"
            style={{ color: member.colorHex, borderColor: member.colorHex }}
            onClick={e => e.stopPropagation()}
          >⟨/⟩ github.com/{member.github}</a>
          <span className="flip-cue">Click to go back ↩</span>
        </div>
      </div>
    </div>
  );
}

function PipelineViz() {
  const [step, setStep] = useState(-1);
  const [running, setRunning] = useState(false);
  const [note, setNote] = useState("Click ▶ Simulate to watch the chatbot think in real-time");
  const run = () => {
    if (running) return;
    setRunning(true); setStep(-1);
    PIPELINE_STEPS.forEach((p, i) => {
      setTimeout(() => {
        setStep(i); setNote(p.note);
        if (i === PIPELINE_STEPS.length - 1) {
          setTimeout(() => { setStep(-1); setRunning(false); setNote("Done! Click ▶ again to replay."); }, 900);
        }
      }, i * 500);
    });
  };
  return (
    <div className="pipeline-wrap">
      <div className="pipeline-topbar">
        <div>
          <div className="section-eyebrow">🤖 How The Chatbot Thinks</div>
          <div className="pipeline-title">RAG Pipeline — Live Simulation</div>
        </div>
        <button className="pipe-btn" onClick={run} disabled={running}>
          {running ? "⏳ Running…" : "▶ Simulate"}
        </button>
      </div>
      <div className="pipeline-track">
        {PIPELINE_STEPS.map((p, i) => (
          <div key={i} className="pstep-group">
            <div className={`pstep ${step === i ? "pstep--active" : ""} ${step > i ? "pstep--done" : ""}`}
              style={{ "--c": p.color }}>
              <div className="pstep-icon">{p.icon}</div>
              <div className="pstep-label">{p.label}</div>
              {step === i && <div className="pstep-ring" />}
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <div className={`pipe-arrow ${step > i ? "pipe-arrow--lit" : ""}`}>→</div>
            )}
          </div>
        ))}
      </div>
      <div className={`pipe-note-bar ${step >= 0 ? "pipe-note-bar--on" : ""}`}>{note}</div>
    </div>
  );
}

function FactTicker() {
  const [idx, setIdx] = useState(0);
  const [fade, setFade] = useState(true);
  useEffect(() => {
    const t = setInterval(() => {
      setFade(false);
      setTimeout(() => { setIdx(i => (i + 1) % FUN_FACTS.length); setFade(true); }, 350);
    }, 3200);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="fact-ticker">
      <span className="fact-badge">💡 Fun Fact</span>
      <span className={`fact-text ${fade ? "fact-in" : "fact-out"}`}>{FUN_FACTS[idx]}</span>
    </div>
  );
}

/* ══════════════════════════════════════════════════
   MAIN
══════════════════════════════════════════════════ */
export default function About() {
  const [activeTab, setActiveTab] = useState("All");
  const [statsRef, statsInView] = useInView(0.2);
  const [treeRef, treeInView]   = useInView(0.05);
  const [stackRef, stackInView] = useInView(0.1);
  const [teamRef, teamInView]   = useInView(0.1);
  const [pipeRef, pipeInView]   = useInView(0.1);
  const [eggCount, setEggCount] = useState(0);
  const [egg, setEgg]           = useState(false);

  const filteredStack = activeTab === "All" ? STACK : STACK.filter(s => s.tab === activeTab);

  const handleBrand = () => {
    const n = eggCount + 1; setEggCount(n);
    if (n >= 5) { setEgg(true); setTimeout(() => { setEgg(false); setEggCount(0); }, 3500); }
  };

  return (
    <div className="about-page">
      <Navbar />
      {egg && <div className="easter-egg">🎉 You found the easter egg! MedScan AI salutes you 🎉</div>}

      {/* HERO */}
      <div className="about-hero">
        <div className="hero-dot-grid" />
        <div className="about-body">
          <div className="about-header anim-up">
            <div className="hero-badge">🔬 Final Year Project · CS Capstone 2026</div>
            <h1>About <span className="hero-brand" onClick={handleBrand}>MedScan AI</span></h1>
            <p>An educational AI platform helping medical students understand how deep learning
              analyzes breast cancer histopathology — through CNN predictions, Grad-CAM heatmaps,
              and a RAG-powered chatbot.</p>
            <FactTicker />
          </div>
          <div className="stats-row" ref={statsRef}>
            {STATS.map((s, i) => <StatCard key={s.label} {...s} delay={i * 80} started={statsInView} />)}
          </div>
        </div>
      </div>

      <div className="about-body">

        {/* MISSION */}
        {/* MISSION */}
<div className="about-mission">
  <div className="mission-left">
    <div className="section-eyebrow">🎯 Our Purpose</div>
    <h2 className="section-h2">Pathology Learning, Simplified.</h2>
    <p>Understanding histopathology can be a daunting task for students. MedScan AI serves as an 
      educational companion designed to help medical students recognize and understand complex 
      tissue patterns more effectively.</p>
    <p>This tool bridges the gap between theoretical knowledge and practical visual analysis. 
      By providing AI-assisted insights and a RAG-powered chatbot, students can refine their 
      observational skills and learn the significance of various pathological features, 
      such as nuclei density and mitotic activity levels.</p>
    <p>It is <strong>not a clinical tool.</strong> Our goal is to make your pathology learning 
      journey more interactive, accessible, and easier to grasp.</p>
  </div>
  <div className="mission-feats">
    {[
      { icon: "📚", t: "Learning Aide",  s: "Understand tissue morphology" },
      { icon: "💡", t: "Visual Insights", s: "Interactive slide analysis" },
      { icon: "💬", t: "Study Partner",  s: "Ask anything about pathology" },
      { icon: "🎓", t: "Academic Focus", s: "Built for medical education" },
    ].map(f => (
      <div className="mfeat" key={f.t}>
        <span className="mfeat-icon">{f.icon}</span>
        <div><div className="mfeat-t">{f.t}</div><div className="mfeat-s">{f.s}</div></div>
      </div>
    ))}
  </div>
</div>

        {/* ARCHITECTURE TREE */}
        <div ref={treeRef} className={`tree-section sr ${treeInView ? "sr--in" : ""}`}>
          <div className="section-eyebrow">🌳 Interactive Explorer</div>
          <div className="tree-top">
            <div>
              <h2 className="section-h2" style={{ marginBottom: "0.2rem" }}>System Architecture Tree</h2>
              <p className="section-sub">Click any branch to expand or collapse</p>
            </div>
            <div className="tree-legend">
              {[["#17c964","Frontend"],["#F5A524","Backend"],["#7828C8","ML Layer"],["#17c964","Chatbot"]].map(([c,l]) => (
                <span key={l} className="legend-item"><i style={{ background: c }} />{l}</span>
              ))}
            </div>
          </div>
          <div className="tree-box">
            <TreeNode node={ARCH_TREE} depth={0} />
          </div>
        </div>

        {/* TECH STACK */}
        <div ref={stackRef} className={`about-stack sr ${stackInView ? "sr--in" : ""}`}>
          <div className="stack-header-row">
            <div>
              <div className="section-eyebrow">⚙️ Built With</div>
              <h2 className="section-h2" style={{ marginBottom: 0 }}>Technology Stack</h2>
            </div>
            <div className="stabs">
              {STACK_TABS.map(tab => (
                <button key={tab} className={`stab ${activeTab === tab ? "stab--on" : ""}`}
                  onClick={() => setActiveTab(tab)}>{tab}</button>
              ))}
            </div>
          </div>
          <div className="stack-grid">
            {filteredStack.map((s, i) => (
              <div className="sitem" key={s.name} style={{ animationDelay: `${i * 45}ms` }}>
                <div className="sitem-ico">{s.icon}</div>
                <div className="sitem-lbl">{s.label}</div>
                <div className="sitem-name">{s.name}</div>
                <div className="sitem-desc">{s.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* TEAM */}
        <div ref={teamRef} className={`sr ${teamInView ? "sr--in" : ""}`}>
          <div className="section-eyebrow" style={{ textAlign: "center" }}>👥 The Builders</div>
          <h2 className="section-h2" style={{ textAlign: "center" }}>Meet The Team</h2>
          <p className="section-sub" style={{ textAlign: "center", marginBottom: "1.5rem" }}>Click a card to flip it</p>
          <div className="team-grid">
            {TEAM.map(m => <TeamCard key={m.name} member={m} />)}
          </div>
        </div>

        {/* PIPELINE */}
        <div ref={pipeRef} className={`sr ${pipeInView ? "sr--in" : ""}`}>
          <PipelineViz />
        </div>

        {/* MODELS */}
        <div className="models-section">
          <div className="section-eyebrow">🧠 Deep Learning</div>
          <h2 className="section-h2">The Three Models</h2>
          <div className="models-grid">
            {[
              { badge: "Model A",  name: "IDC Detection",     arch: "ResNet-18", data: "Kaggle IDC", xai: "Grad-CAM",  icon: "🔬", c: "#17c964", bg: "rgba(23,201,100,.07)" },
              { badge: "Model B1", name: "Nuclei Analysis",   arch: "U-Net",     data: "NuSeC",      xai: "Seg Masks", icon: "🧬", c: "#006FEE", bg: "rgba(0,111,238,.07)"  },
              { badge: "Model B2", name: "Mitosis Detection", arch: "CNN",       data: "MiDeSeC",    xai: "Overlays",  icon: "🔴", c: "#7828C8", bg: "rgba(120,40,200,.07)" },
            ].map(m => (
              <div className="model-card" key={m.badge} style={{ "--mc": m.c, "--mcbg": m.bg }}>
                <div className="model-topbar">
                  <span className="model-ico">{m.icon}</span>
                  <span className="model-badge-pill" style={{ color: m.c, background: m.bg }}>{m.badge}</span>
                </div>
                <div className="model-name">{m.name}</div>
                <div className="model-rows">
                  <div className="model-row"><span>Architecture</span><strong>{m.arch}</strong></div>
                  <div className="model-row"><span>Dataset</span><strong>{m.data}</strong></div>
                  <div className="model-row"><span>Explainability</span><strong>{m.xai}</strong></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* DISCLAIMER */}
        <div className="about-disclaimer">
          <div className="disc-icon">⚠️</div>
          <h3>Educational Use Only</h3>
          <p>MedScan AI is a Final Year Project built solely for academic and educational purposes.
            All datasets are publicly available. No real patient data is collected or processed.
            AI predictions are <strong>not clinical diagnoses</strong> and must never be used
            for any form of medical decision-making.</p>
          <div className="disc-tags">
            {["📚 Academic Project","🔒 No Patient Data","✅ Public Datasets","🎓 FYP 2026"].map(t => (
              <span key={t} className="disc-tag">{t}</span>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}