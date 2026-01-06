import { useState } from "react";
import { safeFetch, pretty } from "../utils/api";
import { useStatus } from "../utils/hooks";

export default function PlayersView() {
  const [players, setPlayers] = useState([]);
  const [limit, setLimit] = useState(25);
  const [status, statusKind, setStatus] = useStatus();
  const [selectedPlayerId, setSelectedPlayerId] = useState("");
  const [season, setSeason] = useState("2023-24");
  const [features, setFeatures] = useState(null);
  const [featuresStatus, featuresStatusKind, setFeaturesStatus] = useStatus();
  const [contextualStats, setContextualStats] = useState(null);
  const [contextualType, setContextualType] = useState("game-situation");
  const [opponentTeamId, setOpponentTeamId] = useState("");
  const [contextualStatus, contextualStatusKind, setContextualStatus] = useStatus();

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

  const loadContextualStats = async () => {
    if (!selectedPlayerId.trim()) {
      setContextualStatus("Enter a player ID.", "error");
      setContextualStats(null);
      return;
    }
    setContextualStatus("Loading contextual stats...");
    setContextualStats(null);
    try {
      const id = encodeURIComponent(selectedPlayerId.trim());
      const seasonParam = season.trim() ? `&season=${encodeURIComponent(season.trim())}` : "";
      
      let url = "";
      if (contextualType === "vs-team") {
        if (!opponentTeamId.trim()) {
          setContextualStatus("Enter an opponent team ID.", "error");
          return;
        }
        url = `/players/${id}/contextual/vs-team?opponent_team_id=${encodeURIComponent(opponentTeamId.trim())}${seasonParam}`;
      } else if (contextualType === "game-situation") {
        url = `/players/${id}/contextual/game-situation${seasonParam ? "?" + seasonParam.substring(1) : ""}`;
      } else if (contextualType === "by-period") {
        url = `/players/${id}/contextual/by-period${seasonParam ? "?" + seasonParam.substring(1) : ""}`;
      }
      
      const res = await safeFetch(url);
      if (!res.ok) {
        setContextualStatus(`Error ${res.status}`, "error");
        setContextualStats(null);
        return;
      }
      setContextualStats(res.data);
      setContextualStatus("Loaded contextual stats.", "success");
    } catch (err) {
      setContextualStatus(`Error: ${err}`, "error");
      setContextualStats(null);
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
          <>
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
                            <td><strong>PER</strong> (Player Efficiency Rating)</td>
                            <td>{features.advanced_stats.player_efficiency_rating?.toFixed(2) || "-"}</td>
                          </tr>
                          <tr>
                            <td><strong>Usage Rate</strong></td>
                            <td>{features.advanced_stats.usage_rate?.toFixed(1) || "-"}%</td>
                          </tr>
                          {features.advanced_stats.box_plus_minus != null && (
                            <tr>
                              <td><strong>BPM</strong> (Box Plus/Minus)</td>
                              <td>{features.advanced_stats.box_plus_minus > 0 ? "+" : ""}{features.advanced_stats.box_plus_minus.toFixed(2)}</td>
                            </tr>
                          )}
                          {features.advanced_stats.value_over_replacement_player != null && (
                            <tr>
                              <td><strong>VORP</strong> (Value Over Replacement)</td>
                              <td>{features.advanced_stats.value_over_replacement_player.toFixed(2)}</td>
                            </tr>
                          )}
                          {features.advanced_stats.win_shares != null && (
                            <tr>
                              <td><strong>Win Shares</strong></td>
                              <td>{features.advanced_stats.win_shares.toFixed(2)}</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            </div>
            
            {/* Clutch Stats */}
            {features.clutch_stats && Object.keys(features.clutch_stats).length > 0 && !features.clutch_stats.error && (
              <div style={{ marginTop: "1.5rem" }}>
                <h3>Clutch Performance</h3>
                <p className="hint" style={{ marginTop: "0.5rem", marginBottom: "0.5rem" }}>
                  Stats in close games (decided by 5 points or less)
                </p>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Clutch Games</strong></td>
                        <td>{features.clutch_stats.clutch_games || 0}</td>
                      </tr>
                      <tr>
                        <td><strong>Clutch PPG</strong></td>
                        <td>{features.clutch_stats.clutch_points_per_game?.toFixed(1) || "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>Clutch RPG</strong></td>
                        <td>{features.clutch_stats.clutch_rebounds_per_game?.toFixed(1) || "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>Clutch APG</strong></td>
                        <td>{features.clutch_stats.clutch_assists_per_game?.toFixed(1) || "-"}</td>
                      </tr>
                      <tr>
                        <td><strong>Clutch FG%</strong></td>
                        <td>{features.clutch_stats.clutch_fg_percentage?.toFixed(1) || "-"}%</td>
                      </tr>
                      <tr>
                        <td><strong>Clutch +/-</strong></td>
                        <td style={{ 
                          color: features.clutch_stats.clutch_plus_minus_per_game > 0 ? "#86efac" : features.clutch_stats.clutch_plus_minus_per_game < 0 ? "#fca5a5" : "#e5e7eb",
                          fontWeight: 600
                        }}>
                          {features.clutch_stats.clutch_plus_minus_per_game > 0 ? "+" : ""}{features.clutch_stats.clutch_plus_minus_per_game?.toFixed(1) || "-"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <h2>Contextual Stats</h2>
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
              Type
              <select
                value={contextualType}
                onChange={(e) => setContextualType(e.target.value)}
              >
                <option value="game-situation">Game Situation</option>
                <option value="vs-team">vs Team</option>
                <option value="by-period">By Period</option>
              </select>
            </label>
            {contextualType === "vs-team" && (
              <label>
                Opponent Team ID
                <input
                  type="number"
                  value={opponentTeamId}
                  onChange={(e) => setOpponentTeamId(e.target.value)}
                  placeholder="e.g. 2"
                />
              </label>
            )}
            <label>
              Season (optional)
              <input
                type="text"
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                placeholder="2023-24"
              />
            </label>
            <button type="button" className="btn primary" onClick={loadContextualStats}>
              Load Contextual Stats
            </button>
          </div>
        </div>
        <div className={`status-bar ${contextualStatusKind}`}>{contextualStatus}</div>
        {contextualStats && (
          <div style={{ marginTop: "1rem" }}>
            {contextualType === "game-situation" && contextualStats.game_situations && (
              <div>
                <h3>Performance by Game Situation</h3>
                <div className="split-columns" style={{ marginTop: "0.5rem" }}>
                  <div>
                    <h4>Close Games (≤5 pts)</h4>
                    <div className="table-container">
                      <table>
                        <tbody>
                          <tr>
                            <td><strong>Games</strong></td>
                            <td>{contextualStats.game_situations.close_games.games}</td>
                          </tr>
                          <tr>
                            <td><strong>PPG</strong></td>
                            <td>{contextualStats.game_situations.close_games.points_per_game}</td>
                          </tr>
                          <tr>
                            <td><strong>RPG</strong></td>
                            <td>{contextualStats.game_situations.close_games.rebounds_per_game}</td>
                          </tr>
                          <tr>
                            <td><strong>APG</strong></td>
                            <td>{contextualStats.game_situations.close_games.assists_per_game}</td>
                          </tr>
                          <tr>
                            <td><strong>FG%</strong></td>
                            <td>{contextualStats.game_situations.close_games.fg_percentage?.toFixed(1) || "-"}%</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div>
                    <h4>Blowout Games (≥20 pts)</h4>
                    <div className="table-container">
                      <table>
                        <tbody>
                          <tr>
                            <td><strong>Games</strong></td>
                            <td>{contextualStats.game_situations.blowout_games.games}</td>
                          </tr>
                          <tr>
                            <td><strong>PPG</strong></td>
                            <td>{contextualStats.game_situations.blowout_games.points_per_game}</td>
                          </tr>
                          <tr>
                            <td><strong>RPG</strong></td>
                            <td>{contextualStats.game_situations.blowout_games.rebounds_per_game}</td>
                          </tr>
                          <tr>
                            <td><strong>APG</strong></td>
                            <td>{contextualStats.game_situations.blowout_games.assists_per_game}</td>
                          </tr>
                          <tr>
                            <td><strong>FG%</strong></td>
                            <td>{contextualStats.game_situations.blowout_games.fg_percentage?.toFixed(1) || "-"}%</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {contextualType === "vs-team" && contextualStats.stats && (
              <div>
                <h3>Performance vs {contextualStats.opponent_team_name}</h3>
                <div className="table-container" style={{ marginTop: "0.5rem" }}>
                  <table>
                    <tbody>
                      <tr>
                        <td><strong>Games</strong></td>
                        <td>{contextualStats.stats.games_played}</td>
                      </tr>
                      <tr>
                        <td><strong>PPG</strong></td>
                        <td>{contextualStats.stats.points_per_game}</td>
                      </tr>
                      <tr>
                        <td><strong>RPG</strong></td>
                        <td>{contextualStats.stats.rebounds_per_game}</td>
                      </tr>
                      <tr>
                        <td><strong>APG</strong></td>
                        <td>{contextualStats.stats.assists_per_game}</td>
                      </tr>
                      <tr>
                        <td><strong>FG%</strong></td>
                        <td>{contextualStats.stats.fg_percentage?.toFixed(1) || "-"}%</td>
                      </tr>
                      <tr>
                        <td><strong>+/-</strong></td>
                        <td style={{ 
                          color: contextualStats.stats.plus_minus_per_game > 0 ? "#86efac" : contextualStats.stats.plus_minus_per_game < 0 ? "#fca5a5" : "#e5e7eb",
                          fontWeight: 600
                        }}>
                          {contextualStats.stats.plus_minus_per_game > 0 ? "+" : ""}{contextualStats.stats.plus_minus_per_game?.toFixed(1) || "-"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {contextualType === "by-period" && contextualStats.monthly_performance && (
              <div>
                <h3>Performance by Month</h3>
                <div className="table-container" style={{ marginTop: "0.5rem" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Month</th>
                        <th>Games</th>
                        <th>PPG</th>
                        <th>RPG</th>
                        <th>APG</th>
                        <th>FG%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(contextualStats.monthly_performance)
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([monthKey, stats]) => (
                          <tr key={monthKey}>
                            <td><strong>{stats.month}</strong></td>
                            <td>{stats.games_played}</td>
                            <td>{stats.points_per_game}</td>
                            <td>{stats.rebounds_per_game}</td>
                            <td>{stats.assists_per_game}</td>
                            <td>{stats.fg_percentage?.toFixed(1) || "-"}%</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

