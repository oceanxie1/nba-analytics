import { useMemo } from "react";
import { API_BASE } from "../utils/api";

export default function Header({ activeView, onChangeView }) {
  const views = useMemo(
    () => [
      { id: "overview", label: "Overview" },
      { id: "players", label: "Players" },
      { id: "compare", label: "Compare Players" },
      { id: "teams", label: "Teams" },
      { id: "compare-teams", label: "Compare Teams" },
      { id: "games", label: "Games" },
    ],
    []
  );

  const docsUrl = `${API_BASE}/docs`;

  return (
    <header className="app-header">
      <div className="logo">
        <span className="logo-accent">NBA</span> Analytics
      </div>
      <nav className="nav-links">
        {views.map((v) => (
          <button
            key={v.id}
            type="button"
            className={`nav-link ${activeView === v.id ? "is-active" : ""}`}
            onClick={() => onChangeView(v.id)}
          >
            {v.label}
          </button>
        ))}
      </nav>
      <a className="docs-link" href={docsUrl} target="_blank" rel="noreferrer">
        Swagger Docs →
      </a>
    </header>
  );
}



