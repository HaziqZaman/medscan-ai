import { useState, useRef, useEffect } from "react";
import Navbar from "../components/Navbar";
import "./chatbot.css";

const SUGGESTIONS = [
  "What is IDC?",
  "How does Grad-CAM work?",
  "Explain tumor grading",
  "What is ResNet-18?",
  "What does confidence score mean?",
];

const BOT_INTRO = {
  id: 0,
  role: "bot",
  text: "Hi! I'm your MedScan AI Assistant. I can help you understand breast cancer histopathology, AI predictions, Grad-CAM explanations, and more. What would you like to learn?",
  time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
};

function Chatbot() {
  const [messages, setMessages] = useState([BOT_INTRO]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const sendMessage = async (text) => {
    const userMsg = {
      id: Date.now(),
      role: "user",
      text,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTyping(true);

    // TODO: Replace with real Django /chat endpoint
    // const res = await fetch("/api/chat", { method: "POST", body: JSON.stringify({ message: text }) });
    // const data = await res.json();

    await new Promise((r) => setTimeout(r, 1200));

    const botReply = {
      id: Date.now() + 1,
      role: "bot",
      text: getMockReply(text),
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setTyping(false);
    setMessages((prev) => [...prev, botReply]);
  };

  const getMockReply = (text) => {
    const t = text.toLowerCase();
    if (t.includes("idc"))
      return "Invasive Ductal Carcinoma (IDC) is the most common type of breast cancer — about 80% of all cases. It starts in the milk ducts but breaks through the duct walls to invade surrounding breast tissue. In histopathology, IDC appears as irregular clusters of malignant cells with abnormal nuclei.";
    if (t.includes("grad-cam") || t.includes("gradcam"))
      return "Grad-CAM (Gradient-weighted Class Activation Mapping) highlights which regions of an input image most influenced the model's prediction. It computes gradients of the predicted class score with respect to feature maps in the last convolutional layer — producing a heatmap overlaid on the image.";
    if (t.includes("resnet"))
      return "ResNet-18 is a deep CNN with 18 layers using residual (skip) connections to combat vanishing gradients. We chose it because it's lightweight, fast, and stable — ideal for this educational tool. We use transfer learning, pre-training on ImageNet and fine-tuning on the IDC dataset.";
    if (t.includes("grading") || t.includes("grade"))
      return "Tumor grading describes how abnormal cancer cells look under a microscope. Grade 1 (well-differentiated) cells look most like normal cells. Grade 3 (poorly differentiated) are highly abnormal and aggressive. Our Model B will classify IDC patches by grade.";
    if (t.includes("confidence"))
      return "The confidence score is the softmax probability output of the final classification layer — a value between 0–100% indicating how certain the model is about its prediction. Higher confidence means the image features more strongly matched the training patterns for that class.";
    return "That's a great question! This feature will be connected to our AI backend. For now, I can explain IDC, Grad-CAM, tumor grading, ResNet-18, and confidence scores. Try asking about one of those!";
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && input.trim()) sendMessage(input.trim());
  };

  return (
    <div className="chatbot-page">
      <Navbar />
      <div className="chatbot-body">

        <div className="chatbot-header">
          <div className="chat-avatar">🤖</div>
          <div>
            <h1>
              <span className="online-dot" />
              MedScan AI Assistant
            </h1>
            <p>Educational guide — histopathology &amp; AI explanations</p>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-bubble ${msg.role}`}>
              <div className="bubble-text">{msg.text}</div>
              <div className="bubble-time">{msg.time}</div>
            </div>
          ))}
          {typing && (
            <div className="chat-bubble bot">
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="chat-suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} className="suggest-chip" onClick={() => sendMessage(s)}>
              {s}
            </button>
          ))}
        </div>

        <div className="chat-input-row">
          <div className="chat-input-wrap">
            <input
              className="chat-input"
              placeholder="Ask about IDC, Grad-CAM, tumor grading..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
            />
          </div>
          <button
            className="chat-send-btn"
            onClick={() => input.trim() && sendMessage(input.trim())}
            disabled={!input.trim() || typing}
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
