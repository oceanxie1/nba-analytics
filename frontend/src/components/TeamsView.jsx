import { useState } from "react";
import { safeFetch, pretty } from "../utils/api";
import { useStatus } from "../utils/hooks";

export default function TeamsView() {
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
          <div style={{ marginTop: "1rem" }}>
            <div className="split-columns">
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
            
            {/* Advanced Metrics */}
            {teamStats.advanced_metrics && (
              <div style={{ marginTop: "1.5rem" }}>
                <h3>Advanced Metrics</h3>
                <div className="table-container" style={{ marginTop: "0.5rem" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Pace</strong></td>
                        <td>{teamStats.advanced_metrics.pace != null ? `${teamStats.advanced_metrics.pace} poss/game` : "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>Offensive Rating</strong></td>
                        <td>{teamStats.advanced_metrics.offensive_rating != null ? `${teamStats.advanced_metrics.offensive_rating} pts/100 poss` : "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>Defensive Rating</strong></td>
                        <td>{teamStats.advanced_metrics.defensive_rating != null ? `${teamStats.advanced_metrics.defensive_rating} pts/100 poss` : "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>Net Rating</strong></td>
                        <td style={{ 
                          color: teamStats.advanced_metrics.net_rating > 0 ? "#86efac" : teamStats.advanced_metrics.net_rating < 0 ? "#fca5a5" : "#e5e7eb",
                          fontWeight: 600
                        }}>
                          {teamStats.advanced_metrics.net_rating != null ? `${teamStats.advanced_metrics.net_rating > 0 ? "+" : ""}${teamStats.advanced_metrics.net_rating} pts/100 poss` : "-"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Four Factors */}
            {teamStats.four_factors && (
              <div style={{ marginTop: "1.5rem" }}>
                <h3>Four Factors</h3>
                <div className="table-container" style={{ marginTop: "0.5rem" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Factor</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>eFG%</strong> (Effective FG%)</td>
                        <td>{teamStats.four_factors.effective_field_goal_percentage != null ? `${teamStats.four_factors.effective_field_goal_percentage}%` : "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>TOV%</strong> (Turnover %)</td>
                        <td>{teamStats.four_factors.turnover_percentage != null ? `${teamStats.four_factors.turnover_percentage}%` : "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>FTA Rate</strong> (FT Attempt Rate)</td>
                        <td>{teamStats.four_factors.free_throw_attempt_rate != null ? `${teamStats.four_factors.free_throw_attempt_rate}%` : "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>ORB%</strong> (Offensive Rebound %)</td>
                        <td style={{ color: "#9ca3af" }}>N/A (data not available)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
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

