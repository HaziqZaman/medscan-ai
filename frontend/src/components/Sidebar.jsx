import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div style={{width:"200px", background:"#eee", padding:"10px"}}>
      <ul>
        <li><Link to="/dashboard">Dashboard</Link></li>
        <li><Link to="/analysis">Analysis</Link></li>
        <li><Link to="/history">Case History</Link></li>
        <li><Link to="/knowledge">Knowledge Center</Link></li>
        <li><Link to="/chatbot">Chatbot</Link></li>
        <li><Link to="/about">About</Link></li>
      </ul>
    </div>
  );
}

export default Sidebar;