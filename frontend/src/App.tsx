import { NavLink, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import GraphExplorerPage from "./pages/GraphExplorerPage";
import ConceptExplorerPage from "./pages/ConceptExplorerPage";
import LearningPathPage from "./pages/LearningPathPage";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/upload", label: "Upload" },
  { to: "/graph", label: "Graph Explorer" },
  { to: "/concepts", label: "Concept Explorer" },
  { to: "/learning-path", label: "Learning Path" },
];

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Local-First Knowledge OS</p>
          <h1>Knowledge Vault</h1>
          <p className="muted">
            Turn personal documents into a navigable concept graph.
          </p>
        </div>
        <nav className="nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/graph" element={<GraphExplorerPage />} />
          <Route path="/concepts" element={<ConceptExplorerPage />} />
          <Route path="/learning-path" element={<LearningPathPage />} />
        </Routes>
      </main>
    </div>
  );
}
