import Navbar from "../components/Navbar";
import "./About.css";

const STACK = [
  { icon: "⚛️", label: "Frontend", name: "React + Vite" },
  { icon: "🐍", label: "Backend", name: "Django" },
  { icon: "⚡", label: "ML API", name: "FastAPI" },
  { icon: "🔥", label: "ML", name: "PyTorch" },
  { icon: "🧠", label: "Model", name: "ResNet-18" },
  { icon: "🗺️", label: "XAI", name: "Grad-CAM" },
  { icon: "📦", label: "Dataset", name: "Kaggle IDC" },
  { icon: "🗄️", label: "Database", name: "SQLite" },
];

const TEAM = [
  {
    name: "Zaman",
    role: "Full Stack Developer",
    tasks: ["System Architecture", "React Frontend", "Backend Integration", "Documentation"],
  },
  {
    name: "Shami Boxer",
    role: "ML Engineer",
    tasks: ["CNN Models", "Dataset Processing", "Model Training", "Grad-CAM"],
  },
];

function About() {
  return (
    <div className="about-page">
      <Navbar />
      <div className="about-body">

        <div className="about-header">
          <h1>About <span>MedScan AI</span></h1>
          <p>
            An educational AI platform built to help medical students and trainees
            understand how deep learning analyzes breast cancer histopathology.
          </p>
        </div>

        <div className="about-mission">
          <h2>Our Mission</h2>
          <p>
            Medical students lack accessible tools to understand how AI interprets histopathology images.
            MedScan AI bridges that gap — providing AI predictions, Grad-CAM explanations,
            and educational content in one platform. It is not a clinical tool. It is a
            window into how AI thinks about cancer tissue.
          </p>
        </div>

        <div className="about-stack">
          <h2>Technology Stack</h2>
          <div className="stack-grid">
            {STACK.map((s) => (
              <div className="stack-item" key={s.name}>
                <div className="stack-item-icon">{s.icon}</div>
                <div className="stack-item-label">{s.label}</div>
                <div className="stack-item-name">{s.name}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="about-team">
          {TEAM.map((member) => (
            <div className="team-card" key={member.name}>
              <div className="team-avatar">👨‍💻</div>
              <div className="team-name">{member.name}</div>
              <div className="team-role">{member.role}</div>
              <div className="team-tasks">
                {member.tasks.map((t) => (
                  <span className="team-task" key={t}>{t}</span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="about-disclaimer">
          <h3>⚠️ Educational Use Only</h3>
          <p>
            MedScan AI is a Final Year Project developed for academic purposes only.
            All datasets are public. No real patient data is used. AI predictions are
            not clinical diagnoses and must never be used for medical decision-making.
          </p>
        </div>

      </div>
    </div>
  );
}

export default About;
