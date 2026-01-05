import { useState } from "react";
import { safeFetch, pretty } from "../utils/api";
import { useStatus } from "../utils/hooks";

export default function GamesView() {
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

