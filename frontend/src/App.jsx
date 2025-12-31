import React, { useCallback, useMemo, useState } from "react";
import "./styles.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "") || "http://127.0.0.1:8000";

async function safeFetch(path) {
  const url = `${API_BASE}${path}`;
  const resp = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
  });
  const text = await resp.text();
  try {
    return { ok: resp.ok, status: resp.status, data: JSON.parse(text) };
  } catch {
    return { ok: resp.ok, status: resp.status, data: text };
  }
}

function pretty(value) {
  if (value == null || value === "") return "";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function useStatus() {
  const [message, setMessage] = useState("");
  const [kind, setKind] = useState("");
  const set = useCallback((msg, k = "") => {
    setMessage(msg);
    setKind(k);
  }, []);
  return [message, kind, set];
}

function Header({ activeView, onChangeView }) {
  const views = useMemo(
    () => [
      { id: "overview", label: "Overview" },
      { id: "players", label: "Players" },
      { id: "teams", label: "Teams" },
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

function OverviewView() {
  const [healthOutput, setHealthOutput] = useState("");

  const runHealthCheck = async () => {
    setHealthOutput("Checking /health ...");
    try {
      const res = await safeFetch("/health");
      setHealthOutput(`Status ${res.status}\n${pretty(res.data)}`);
    } catch (err) {
      setHealthOutput(`Error: ${err}`);
    }
  };

  return (
    <section className="view is-visible">
      <div className="grid-2">
        <div className="card">
          <h2>Welcome</h2>
          <p>
            This React UI lets you explore the <strong>NBA Analytics API</strong> without
            touching Swagger or curl.
          </p>
          <ul className="bullet-list">
            <li>Run quick health checks</li>
            <li>Browse players and teams</li>
            <li>Inspect games</li>
          </ul>
          <button type="button" className="btn primary" onClick={runHealthCheck}>
            Run Health Check
          </button>
          <pre className="code-block small muted">{healthOutput}</pre>
        </div>
        <div className="card">
          <h2>API Base</h2>
          <p className="hint">
            Current API base URL:
            <br />
            <code>{API_BASE}</code>
          </p>
          <p className="hint">
            Change via <code>VITE_API_BASE_URL</code> env var when running Vite.
          </p>
        </div>
      </div>
    </section>
  );
}

function PlayersView() {
  const [players, setPlayers] = useState([]);
  const [limit, setLimit] = useState(25);
  const [status, statusKind, setStatus] = useStatus();
  const [selectedPlayerId, setSelectedPlayerId] = useState("");
  const [season, setSeason] = useState("2023-24");
  const [features, setFeatures] = useState(null);
  const [featuresStatus, featuresStatusKind, setFeaturesStatus] = useStatus();

  const loadPlayers = async () => {
    const safeLimit = Number(limit) || 25;
    setStatus("Loading players...");
    try {
      const res = await safeFetch(`/players?skip=0&limit=${encodeURIComponent(safeLimit)}`);
      if (!res.ok) {
        setStatus(`Error ${res.status}`, "error");
        setPlayers([]);
        return;
      }
      setPlayers(Array.isArray(res.data) ? res.data : []);
      setStatus(`Loaded ${Array.isArray(res.data) ? res.data.length : 0} players`, "success");
    } catch (err) {
      setStatus(`Error: ${err}`, "error");
      setPlayers([]);
    }
  };

  const loadPlayerFeatures = async () => {
    if (!selectedPlayerId.trim()) {
      setFeaturesStatus("Enter a player ID.", "error");
      setFeatures(null);
      return;
    }
    setFeaturesStatus("Loading features...");
    setFeatures(null);
    try {
      const id = encodeURIComponent(selectedPlayerId.trim());
      const seasonParam = season.trim() ? `?season=${encodeURIComponent(season.trim())}` : "";
      const res = await safeFetch(`/players/${id}/features${seasonParam}`);
      if (!res.ok) {
        setFeaturesStatus(`Error ${res.status}`, "error");
        setFeatures(null);
        return;
      }
      setFeatures(res.data);
      setFeaturesStatus("Loaded player features.", "success");
    } catch (err) {
      setFeaturesStatus(`Error: ${err}`, "error");
      setFeatures(null);
    }
  };

  return (
    <section className="view is-visible">
      <div className="card">
        <div className="card-header">
          <h2>Players</h2>
          <div className="controls-row">
            <label>
              Limit
              <input
                type="number"
                min={1}
                max={200}
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
              />
            </label>
            <button type="button" className="btn primary" onClick={loadPlayers}>
              Load Players
            </button>
          </div>
        </div>
        <div className={`status-bar ${statusKind}`}>{status}</div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Team</th>
                <th>Position</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.full_name || p.name}</td>
                  <td>{p.team_abbreviation || p.team_name}</td>
                  <td>{p.position}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <h2>Player Features & Analytics</h2>
          <div className="controls-row">
            <label>
              Player ID
              <input
                type="number"
                value={selectedPlayerId}
                onChange={(e) => setSelectedPlayerId(e.target.value)}
                placeholder="e.g. 1"
              />
            </label>
            <label>
              Season (optional)
              <input
                type="text"
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                placeholder="2023-24"
              />
            </label>
            <button type="button" className="btn primary" onClick={loadPlayerFeatures}>
              Load Features
            </button>
          </div>
        </div>
        <div className={`status-bar ${featuresStatusKind}`}>{featuresStatus}</div>
        {features && (
          <div className="split-columns" style={{ marginTop: "1rem" }}>
            <div>
              <h3>Overview</h3>
              <pre className="code-block small">
                {pretty({
                  player: features.player_name,
                  season: features.season || "Career",
                  games_played: features.games_played,
                })}
              </pre>
              {features.per_game && (
                <>
                  <h3 style={{ marginTop: "1rem" }}>Per Game</h3>
                  <pre className="code-block small">{pretty(features.per_game)}</pre>
                </>
              )}
            </div>
            <div>
              {features.shooting_percentages && (
                <>
                  <h3>Shooting %</h3>
                  <pre className="code-block small">{pretty(features.shooting_percentages)}</pre>
                </>
              )}
              {features.advanced_stats && (
                <>
                  <h3 style={{ marginTop: "1rem" }}>Advanced Stats</h3>
                  <pre className="code-block small">{pretty(features.advanced_stats)}</pre>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function TeamsView() {
  const [teams, setTeams] = useState([]);
  const [status, statusKind, setStatus] = useStatus();

  const loadTeams = async () => {
    setStatus("Loading teams...");
    try {
      const res = await safeFetch("/teams");
      if (!res.ok) {
        setStatus(`Error ${res.status}`, "error");
        setTeams([]);
        return;
      }
      setTeams(Array.isArray(res.data) ? res.data : []);
      setStatus(`Loaded ${Array.isArray(res.data) ? res.data.length : 0} teams`, "success");
    } catch (err) {
      setStatus(`Error: ${err}`, "error");
      setTeams([]);
    }
  };

  return (
    <section className="view is-visible">
      <div className="card">
        <div className="card-header">
          <h2>Teams</h2>
          <button type="button" className="btn primary" onClick={loadTeams}>
            Load Teams
          </button>
        </div>
        <div className={`status-bar ${statusKind}`}>{status}</div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Abbr</th>
                <th>Name</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.abbreviation}</td>
                  <td>{t.name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function GamesView() {
  const [gameId, setGameId] = useState("");
  const [status, statusKind, setStatus] = useStatus();
  const [details, setDetails] = useState("");
  const [boxDetails, setBoxDetails] = useState("");

  const loadGame = async () => {
    if (!gameId.trim()) {
      setStatus("Enter a game ID (from your DB).", "error");
      setDetails("");
      setBoxDetails("");
      return;
    }
    setStatus(`Loading game ${gameId}...`);
    setDetails("");
    setBoxDetails("");
    try {
      const id = encodeURIComponent(gameId.trim());
      const [gameRes, boxRes] = await Promise.all([
        safeFetch(`/games/${id}`),
        safeFetch(`/games/${id}/box-scores`),
      ]);

      setDetails(`Status ${gameRes.status}\n${pretty(gameRes.data)}`);
      setBoxDetails(`Status ${boxRes.status}\n${pretty(boxRes.data)}`);

      if (gameRes.ok) {
        setStatus("Loaded game and box scores.", "success");
      } else {
        setStatus(`Error ${gameRes.status}`, "error");
      }
    } catch (err) {
      setStatus(`Error: ${err}`, "error");
      setDetails("");
      setBoxDetails("");
    }
  };

  return (
    <section className="view is-visible">
      <div className="card">
        <div className="card-header">
          <h2>Games</h2>
          <div className="controls-row">
            <label>
              Game ID
              <input
                type="number"
                value={gameId}
                onChange={(e) => setGameId(e.target.value)}
                placeholder="e.g. 1"
              />
            </label>
            <button type="button" className="btn" onClick={loadGame}>
              Load Game
            </button>
          </div>
        </div>
        <div className={`status-bar ${statusKind}`}>{status}</div>
        <div className="split-columns">
          <div>
            <h3>Game Details</h3>
            <pre className="code-block small">{details}</pre>
          </div>
          <div>
            <h3>Box Scores (raw)</h3>
            <pre className="code-block small">{boxDetails}</pre>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [activeView, setActiveView] = useState("overview");

  return (
    <div className="app-root">
      <Header activeView={activeView} onChangeView={setActiveView} />
      <main className="app-main">
        {activeView === "overview" && <OverviewView />}
        {activeView === "players" && <PlayersView />}
        {activeView === "teams" && <TeamsView />}
        {activeView === "games" && <GamesView />}
      </main>
      <footer className="app-footer">
        <span>NBA Analytics API</span>
        <span className="divider">•</span>
        <span>Backend v0.1.0</span>
      </footer>
    </div>
  );
}


