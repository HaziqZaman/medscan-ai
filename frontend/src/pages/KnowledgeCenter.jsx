import { useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import KnowledgeTable from "../components/KnowledgeTable";
import TOPICS from "../data/knowledgeTopics";
import "./KnowledgeCenter.css";

const CATEGORIES = [
  "All",
  "Basics",
  "Types",
  "Symptoms & Risk",
  "Diagnosis",
  "Histopathology",
  "Staging & Grading",
  "Treatment",
  "AI in MedScan",
];

function KnowledgeCenter() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [selectedTopic, setSelectedTopic] = useState(TOPICS[0] || null);

  const filteredTopics = useMemo(() => {
    const term = search.trim().toLowerCase();

    return TOPICS.filter((topic) => {
      const matchesCategory =
        category === "All" || topic.category === category;

      const matchesSearch =
        !term ||
        topic.title.toLowerCase().includes(term) ||
        topic.summary.toLowerCase().includes(term) ||
        topic.subcategory.toLowerCase().includes(term) ||
        topic.description.some((para) =>
          para.toLowerCase().includes(term)
        ) ||
        topic.keywords.some((keyword) =>
          keyword.toLowerCase().includes(term)
        );

      return matchesCategory && matchesSearch;
    });
  }, [search, category]);

  const handleSelectTopic = (topic) => {
    setSelectedTopic(topic);
  };

  return (
    <div className="knowledge-page">
      <Navbar />

      <div className="knowledge-body">
        <div className="knowledge-header">
          <h1>
            Knowledge <span>Center</span>
          </h1>
          <p>
            Explore structured breast cancer knowledge with searchable topics,
            detailed explanations, and educational references.
          </p>
        </div>

        <div className="knowledge-controls">
          <input
            type="text"
            className="knowledge-search"
            placeholder="Search topics, keywords, category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <div className="knowledge-tabs">
            {CATEGORIES.map((item) => (
              <button
                key={item}
                className={`tab-btn ${category === item ? "active" : ""}`}
                onClick={() => setCategory(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="knowledge-meta">
          <span>{filteredTopics.length} topic(s) found</span>
        </div>

        <KnowledgeTable
          data={filteredTopics}
          onSelect={handleSelectTopic}
          selectedId={selectedTopic?.id}
        />

        <div className="knowledge-detail">
          {selectedTopic ? (
            <>
              <div className="detail-top">
                <div>
                  <span className="detail-badge">{selectedTopic.category}</span>
                  <h2>{selectedTopic.title}</h2>
                  <p className="detail-subcategory">
                    {selectedTopic.subcategory}
                  </p>
                </div>
              </div>

              <p className="detail-summary">{selectedTopic.summary}</p>

              <div className="detail-description">
                {selectedTopic.description.map((para, index) => (
                  <p key={index}>{para}</p>
                ))}
              </div>

              <div className="detail-keywords">
                {selectedTopic.keywords.map((keyword, index) => (
                  <span key={index} className="keyword-chip">
                    {keyword}
                  </span>
                ))}
              </div>

              <div className="detail-source">
                <strong>Source:</strong> {selectedTopic.source}
                {selectedTopic.sourceUrl && (
                  <>
                    {" "}
                    —{" "}
                    <a
                      href={selectedTopic.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View reference
                    </a>
                  </>
                )}
              </div>
            </>
          ) : (
            <div className="knowledge-empty">
              <p>Select a topic to view details.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default KnowledgeCenter;