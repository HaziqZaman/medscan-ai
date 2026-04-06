import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Analysis from "./pages/Analysis";
import CaseHistory from "./pages/CaseHistory";
import KnowledgeCenter from "./pages/KnowledgeCenter";
import Chatbot from "./pages/Chatbot";
import Register from "./pages/Register";
import About from "./pages/About";
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/landing" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/history" element={<CaseHistory />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/knowledge" element={<KnowledgeCenter />} />
        <Route path="/register" element={<Register />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
