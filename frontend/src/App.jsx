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
  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [season, setSeason] = useState("2023-24");
  const [teamStats, setTeamStats] = useState(null);
  const [teamStatsStatus, teamStatsStatusKind, setTeamStatsStatus] = useStatus();
  const [teamGames, setTeamGames] = useState([]);
  const [gamesStatus, gamesStatusKind, setGamesStatus] = useStatus();
  const [selectedGameId, setSelectedGameId] = useState("");
  const [gameStats, setGameStats] = useState(null);
  const [gameStatsStatus, gameStatsStatusKind, setGameStatsStatus] = useStatus();

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

  const loadTeamStats = async () => {
    if (!selectedTeamId.trim()) {
      setTeamStatsStatus("Enter a team ID.", "error");
      setTeamStats(null);
      return;
    }
    setTeamStatsStatus("Loading team stats...");
    setTeamStats(null);
    try {
      const id = encodeURIComponent(selectedTeamId.trim());
      const seasonParam = season.trim() ? encodeURIComponent(season.trim()) : "2023-24";
      const res = await safeFetch(`/teams/${id}/stats/${seasonParam}`);
      if (res.ok) {
        setTeamStats(res.data);
        setTeamStatsStatus("Loaded team stats.", "success");
      } else {
        setTeamStatsStatus(`Error ${res.status}: ${res.data?.detail || res.data}`, "error");
        setTeamStats(null);
      }
    } catch (err) {
      setTeamStatsStatus(`Error: ${err}`, "error");
      setTeamStats(null);
    }
  };

  const loadTeamGames = async () => {
    if (!selectedTeamId.trim()) {
      setGamesStatus("Enter a team ID.", "error");
      setTeamGames([]);
      return;
    }
    setGamesStatus("Loading team games...");
    setTeamGames([]);
    try {
      const id = encodeURIComponent(selectedTeamId.trim());
      const seasonParam = season.trim() ? `?season=${encodeURIComponent(season.trim())}` : "";
      const res = await safeFetch(`/teams/${id}/games${seasonParam}`);
      if (res.ok) {
        setTeamGames(Array.isArray(res.data) ? res.data : []);
        setGamesStatus(`Loaded ${Array.isArray(res.data) ? res.data.length : 0} games`, "success");
      } else {
        setGamesStatus(`Error ${res.status}`, "error");
        setTeamGames([]);
      }
    } catch (err) {
      setGamesStatus(`Error: ${err}`, "error");
      setTeamGames([]);
    }
  };

  const loadGameStats = async () => {
    if (!selectedTeamId.trim() || !selectedGameId.trim()) {
      setGameStatsStatus("Enter both team ID and game ID.", "error");
      setGameStats(null);
      return;
    }
    setGameStatsStatus("Loading game stats...");
    setGameStats(null);
    try {
      const teamId = encodeURIComponent(selectedTeamId.trim());
      const gameId = encodeURIComponent(selectedGameId.trim());
      const res = await safeFetch(`/teams/${teamId}/games/${gameId}/stats`);
      if (!res.ok) {
        setGameStatsStatus(`Error ${res.status}: ${res.data?.detail || res.data}`, "error");
        setGameStats(null);
        return;
      }
      setGameStats(res.data);
      setGameStatsStatus("Loaded game stats.", "success");
    } catch (err) {
      setGameStatsStatus(`Error: ${err}`, "error");
      setGameStats(null);
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
                <th>City</th>
                <th>Conference</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.abbreviation}</td>
                  <td>{t.name}</td>
                  <td>{t.city}</td>
                  <td>{t.conference || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <h2>Team Season Stats</h2>
          <div className="controls-row">
            <label>
              Team ID
              <input
                type="number"
                value={selectedTeamId}
                onChange={(e) => setSelectedTeamId(e.target.value)}
                placeholder="e.g. 1"
              />
            </label>
            <label>
              Season
              <input
                type="text"
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                placeholder="2023-24"
              />
            </label>
            <button type="button" className="btn primary" onClick={loadTeamStats}>
              Load Stats
            </button>
          </div>
        </div>
        <div className={`status-bar ${teamStatsStatusKind}`}>{teamStatsStatus}</div>
        {teamStats && (
          <div className="split-columns" style={{ marginTop: "1rem" }}>
            <div>
              <h3>Record</h3>
              <pre className="code-block small">{pretty(teamStats.record)}</pre>
              <h3 style={{ marginTop: "1rem" }}>Per Game</h3>
              <pre className="code-block small">{pretty(teamStats.per_game)}</pre>
            </div>
            <div>
              <h3>Shooting %</h3>
              <pre className="code-block small">{pretty(teamStats.shooting_percentages)}</pre>
              {teamStats.totals && (
                <>
                  <h3 style={{ marginTop: "1rem" }}>Season Totals</h3>
                  <pre className="code-block small">{pretty({
                    points: teamStats.totals.points,
                    rebounds: teamStats.totals.rebounds,
                    assists: teamStats.totals.assists,
                    games_played: teamStats.games_played
                  })}</pre>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <h2>Team Games</h2>
          <div className="controls-row">
            <label>
              Team ID
              <input
                type="number"
                value={selectedTeamId}
                onChange={(e) => setSelectedTeamId(e.target.value)}
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
            <button type="button" className="btn primary" onClick={loadTeamGames}>
              Load Games
            </button>
          </div>
        </div>
        <div className={`status-bar ${gamesStatusKind}`}>{gamesStatus}</div>
        {teamGames.length > 0 && (
          <div className="table-container" style={{ marginTop: "1rem" }}>
            <table>
              <thead>
                <tr>
                  <th>Game ID</th>
                  <th>Date</th>
                  <th>Home</th>
                  <th>Away</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {teamGames.map((game) => {
                  const isHome = game.home_team_id === parseInt(selectedTeamId);
                  const teamScore = isHome ? game.home_score : game.away_score;
                  const oppScore = isHome ? game.away_score : game.home_score;
                  return (
                    <tr key={game.id}>
                      <td>{game.id}</td>
                      <td>{game.game_date}</td>
                      <td>{game.home_team?.name || `Team ${game.home_team_id}`}</td>
                      <td>{game.away_team?.name || `Team ${game.away_team_id}`}</td>
                      <td>
                        {teamScore !== null && oppScore !== null
                          ? `${teamScore} - ${oppScore}`
                          : "TBD"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <h2>Game Team Stats</h2>
          <div className="controls-row">
            <label>
              Team ID
              <input
                type="number"
                value={selectedTeamId}
                onChange={(e) => setSelectedTeamId(e.target.value)}
                placeholder="e.g. 1"
              />
            </label>
            <label>
              Game ID
              <input
                type="number"
                value={selectedGameId}
                onChange={(e) => setSelectedGameId(e.target.value)}
                placeholder="e.g. 1"
              />
            </label>
            <button type="button" className="btn primary" onClick={loadGameStats}>
              Load Game Stats
            </button>
          </div>
        </div>
        <div className={`status-bar ${gameStatsStatusKind}`}>{gameStatsStatus}</div>
        {gameStats && (
          <div className="split-columns" style={{ marginTop: "1rem" }}>
            <div>
              <h3>Game Info</h3>
              <pre className="code-block small">
                {pretty({
                  game_id: gameStats.game_id,
                  game_date: gameStats.game_date,
                  is_home: gameStats.is_home,
                  team_score: gameStats.team_score,
                  opponent_score: gameStats.opponent_score,
                  won: gameStats.won
                })}
              </pre>
            </div>
            <div>
              <h3>Game Stats</h3>
              <pre className="code-block small">{pretty(gameStats.stats)}</pre>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function GamesView() {
  const [gameId, setGameId] = useState("");
  const [status, statusKind, setStatus] = useStatus();
  const [details, setDetails] = useState("");
  const [boxDetails, setBoxDetails] = useState("");
  const [gameSummary, setGameSummary] = useState(null);
  const [teamStats, setTeamStats] = useState(null);
  const [summaryStatus, summaryStatusKind, setSummaryStatus] = useStatus();

  const loadGame = async () => {
    if (!gameId.trim()) {
      setStatus("Enter a game ID (from your DB).", "error");
      setDetails("");
      setBoxDetails("");
      setGameSummary(null);
      setTeamStats(null);
      return;
    }
    setStatus(`Loading game ${gameId}...`);
    setDetails("");
    setBoxDetails("");
    setGameSummary(null);
    setTeamStats(null);
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

  const loadGameSummary = async () => {
    if (!gameId.trim()) {
      setSummaryStatus("Enter a game ID.", "error");
      setGameSummary(null);
      setTeamStats(null);
      return;
    }
    setSummaryStatus("Loading game summary...");
    setGameSummary(null);
    setTeamStats(null);
    try {
      const id = encodeURIComponent(gameId.trim());
      const res = await safeFetch(`/games/${id}/summary`);
      if (res.ok) {
        setGameSummary(res.data);
        setSummaryStatus("Loaded game summary.", "success");
      } else {
        setSummaryStatus(`Error ${res.status}: ${res.data?.detail || res.data}`, "error");
        setGameSummary(null);
      }
    } catch (err) {
      setSummaryStatus(`Error: ${err}`, "error");
      setGameSummary(null);
    }
  };

  const loadTeamStats = async () => {
    if (!gameId.trim()) {
      setSummaryStatus("Enter a game ID.", "error");
      setTeamStats(null);
      return;
    }
    setSummaryStatus("Loading team stats...");
    setTeamStats(null);
    try {
      const id = encodeURIComponent(gameId.trim());
      const res = await safeFetch(`/games/${id}/team-stats`);
      if (res.ok) {
        setTeamStats(res.data);
        setSummaryStatus("Loaded team stats.", "success");
      } else {
        setSummaryStatus(`Error ${res.status}: ${res.data?.detail || res.data}`, "error");
        setTeamStats(null);
      }
    } catch (err) {
      setSummaryStatus(`Error: ${err}`, "error");
      setTeamStats(null);
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
            <button type="button" className="btn primary" onClick={loadGameSummary}>
              Load Summary
            </button>
            <button type="button" className="btn primary" onClick={loadTeamStats}>
              Team Stats
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

      {gameSummary && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <div className="card-header">
            <h2>Game Summary</h2>
          </div>
          <div className={`status-bar ${summaryStatusKind}`}>{summaryStatus}</div>
          <div className="split-columns" style={{ marginTop: "1rem" }}>
            <div>
              <h3>Game Info</h3>
              <pre className="code-block small">{pretty(gameSummary.game)}</pre>
              <h3 style={{ marginTop: "1rem" }}>Box Scores ({gameSummary.box_score_count})</h3>
              <div className="table-container" style={{ maxHeight: "300px", overflowY: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Player</th>
                      <th>PTS</th>
                      <th>REB</th>
                      <th>AST</th>
                      <th>MIN</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gameSummary.box_scores.slice(0, 10).map((bs) => (
                      <tr key={bs.id}>
                        <td>{bs.player_name || `Player ${bs.player_id}`}</td>
                        <td>{bs.points || 0}</td>
                        <td>{bs.rebounds || 0}</td>
                        <td>{bs.assists || 0}</td>
                        <td>{bs.minutes ? bs.minutes.toFixed(1) : "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {gameSummary.box_scores.length > 10 && (
                <p className="hint" style={{ marginTop: "0.5rem" }}>
                  Showing first 10 of {gameSummary.box_scores.length} box scores
                </p>
              )}
            </div>
            <div>
              <h3>Team Stats</h3>
              {gameSummary.team_stats?.home && (
                <>
                  <h4 style={{ marginTop: "0.5rem", color: "#0ea5e9" }}>
                    {gameSummary.team_stats.home.team_name || "Home Team"}
                  </h4>
                  <pre className="code-block small">{pretty(gameSummary.team_stats.home.stats)}</pre>
                </>
              )}
              {gameSummary.team_stats?.away && (
                <>
                  <h4 style={{ marginTop: "1rem", color: "#f97316" }}>
                    {gameSummary.team_stats.away.team_name || "Away Team"}
                  </h4>
                  <pre className="code-block small">{pretty(gameSummary.team_stats.away.stats)}</pre>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {teamStats && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <div className="card-header">
            <h2>Team Stats Comparison</h2>
          </div>
          <div className={`status-bar ${summaryStatusKind}`}>{summaryStatus}</div>
          <div className="split-columns" style={{ marginTop: "1rem" }}>
            <div>
              <h3 style={{ color: "#0ea5e9" }}>
                {teamStats.home_team?.team_name || "Home Team"}
              </h3>
              <pre className="code-block small">{pretty(teamStats.home_team)}</pre>
            </div>
            <div>
              <h3 style={{ color: "#f97316" }}>
                {teamStats.away_team?.team_name || "Away Team"}
              </h3>
              <pre className="code-block small">{pretty(teamStats.away_team)}</pre>
            </div>
          </div>
        </div>
      )}
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


