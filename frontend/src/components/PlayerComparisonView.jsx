import { useState } from "react";
import { safeFetch } from "../utils/api";
import { useStatus } from "../utils/hooks";

export default function PlayerComparisonView() {
  const [players, setPlayers] = useState([]);
  const [status, statusKind, setStatus] = useStatus();
  const [playerIds, setPlayerIds] = useState("");
  const [season, setSeason] = useState("2023-24");
  const [comparison, setComparison] = useState(null);
  const [comparisonStatus, comparisonStatusKind, setComparisonStatus] = useStatus();

  const loadPlayers = async () => {
    setStatus("Loading players...");
    try {
      const res = await safeFetch("/players?limit=100");
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

  const loadComparison = async () => {
    if (!playerIds.trim()) {
      setComparisonStatus("Enter player IDs (comma-separated).", "error");
      setComparison(null);
      return;
    }
    
    // Validate player IDs
    const ids = playerIds.split(",").map(id => id.trim()).filter(id => id);
    if (ids.length < 2) {
      setComparisonStatus("Enter at least 2 player IDs.", "error");
      setComparison(null);
      return;
    }
    if (ids.length > 10) {
      setComparisonStatus("Maximum 10 players can be compared.", "error");
      setComparison(null);
      return;
    }

    setComparisonStatus("Loading comparison...");
    setComparison(null);
    try {
      const idsParam = ids.join(",");
      const seasonParam = season.trim() || "2023-24";
      const res = await safeFetch(`/players/compare?player_ids=${encodeURIComponent(idsParam)}&season=${encodeURIComponent(seasonParam)}`);
      if (res.ok) {
        setComparison(res.data);
        setComparisonStatus(`Loaded comparison for ${res.data.players.length} players.`, "success");
      } else {
        setComparisonStatus(`Error ${res.status}: ${res.data?.detail || res.data}`, "error");
        setComparison(null);
      }
    } catch (err) {
      setComparisonStatus(`Error: ${err}`, "error");
      setComparison(null);
    }
  };

  // Helper to check if a stat value is best/worst
  const getStatClass = (statKey, playerIndex, value) => {
    if (!comparison?.comparisons || value == null) return "";
    const comp = comparison.comparisons[statKey];
    if (!comp) return "";
    // Compare with tolerance for floating point values
    const tolerance = 0.01;
    const isBest = comp.best?.player_index === playerIndex && 
                   Math.abs((comp.best?.value || 0) - (value || 0)) < tolerance;
    const isWorst = comp.worst?.player_index === playerIndex && 
                    Math.abs((comp.worst?.value || 0) - (value || 0)) < tolerance;
    if (isBest) return "best";
    if (isWorst) return "worst";
    return "";
  };

  return (
    <section className="view is-visible">
      <div className="card">
        <div className="card-header">
          <h2>Player List (Reference)</h2>
          <button type="button" className="btn" onClick={loadPlayers}>
            Load Players
          </button>
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
              {players.slice(0, 50).map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.full_name || p.name}</td>
                  <td>{p.team_abbreviation || p.team_name || "-"}</td>
                  <td>{p.position || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {players.length > 50 && (
          <p className="hint" style={{ marginTop: "0.5rem" }}>
            Showing first 50 of {players.length} players
          </p>
        )}
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <h2>Player Comparison</h2>
          <div className="controls-row">
            <label>
              Player IDs (comma-separated)
              <input
                type="text"
                value={playerIds}
                onChange={(e) => setPlayerIds(e.target.value)}
                placeholder="e.g. 1,2,3"
                style={{ width: "200px" }}
              />
            </label>
            <label>
              Season
              <input
                type="text"
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                placeholder="2023-24"
                style={{ width: "120px" }}
              />
            </label>
            <button type="button" className="btn primary" onClick={loadComparison}>
              Compare Players
            </button>
          </div>
        </div>
        <div className={`status-bar ${comparisonStatusKind}`}>{comparisonStatus}</div>
        <p className="hint" style={{ marginTop: "0.5rem" }}>
          Enter 2-10 player IDs separated by commas. Best stats are highlighted in green, worst in red.
        </p>
      </div>

      {comparison && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <div className="card-header">
            <h2>Comparison Results - {comparison.season}</h2>
          </div>
          
          {/* Per-Game Stats */}
          <div style={{ marginTop: "1.5rem" }}>
            <h3>Per-Game Statistics</h3>
            <div className="table-container" style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Player</th>
                    <th>Games</th>
                    <th>PTS</th>
                    <th>REB</th>
                    <th>AST</th>
                    <th>STL</th>
                    <th>BLK</th>
                    <th>TOV</th>
                    <th>MIN</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.players.map((player, idx) => (
                    <tr key={player.player_id}>
                      <td style={{ fontWeight: 600 }}>{player.player_name}</td>
                      <td>{player.games_played}</td>
                      <td className={getStatClass("per_game_points", idx, player.per_game?.points)}>
                        {player.per_game?.points?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_rebounds", idx, player.per_game?.rebounds)}>
                        {player.per_game?.rebounds?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_assists", idx, player.per_game?.assists)}>
                        {player.per_game?.assists?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_steals", idx, player.per_game?.steals)}>
                        {player.per_game?.steals?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_blocks", idx, player.per_game?.blocks)}>
                        {player.per_game?.blocks?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_turnovers", idx, player.per_game?.turnovers)}>
                        {player.per_game?.turnovers?.toFixed(1) || "-"}
                      </td>
                      <td>{player.per_game?.minutes?.toFixed(1) || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Shooting Percentages */}
          <div style={{ marginTop: "2rem" }}>
            <h3>Shooting Percentages</h3>
            <div className="table-container" style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Player</th>
                    <th>FG%</th>
                    <th>3P%</th>
                    <th>FT%</th>
                    <th>eFG%</th>
                    <th>TS%</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.players.map((player, idx) => (
                    <tr key={player.player_id}>
                      <td style={{ fontWeight: 600 }}>{player.player_name}</td>
                      <td className={getStatClass("shooting_field_goal_percentage", idx, player.shooting_percentages?.field_goal_percentage)}>
                        {player.shooting_percentages?.field_goal_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_three_point_percentage", idx, player.shooting_percentages?.three_point_percentage)}>
                        {player.shooting_percentages?.three_point_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_free_throw_percentage", idx, player.shooting_percentages?.free_throw_percentage)}>
                        {player.shooting_percentages?.free_throw_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_effective_field_goal_percentage", idx, player.shooting_percentages?.effective_field_goal_percentage)}>
                        {player.shooting_percentages?.effective_field_goal_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_true_shooting_percentage", idx, player.shooting_percentages?.true_shooting_percentage)}>
                        {player.shooting_percentages?.true_shooting_percentage?.toFixed(1) || "-"}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Advanced Stats */}
          <div style={{ marginTop: "2rem" }}>
            <h3>Advanced Statistics</h3>
            <div className="table-container" style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Player</th>
                    <th>PER</th>
                    <th>Usage Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.players.map((player, idx) => (
                    <tr key={player.player_id}>
                      <td style={{ fontWeight: 600 }}>{player.player_name}</td>
                      <td className={getStatClass("advanced_player_efficiency_rating", idx, player.advanced_stats?.player_efficiency_rating)}>
                        {player.advanced_stats?.player_efficiency_rating?.toFixed(2) || "-"}
                      </td>
                      <td className={getStatClass("advanced_usage_rate", idx, player.advanced_stats?.usage_rate)}>
                        {player.advanced_stats?.usage_rate?.toFixed(1) || "-"}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Comparison Highlights */}
          {Object.keys(comparison.comparisons || {}).length > 0 && (
            <div style={{ marginTop: "2rem", padding: "1rem", background: "rgba(15, 23, 42, 0.7)", borderRadius: "0.5rem" }}>
              <h3>Key Highlights</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem", marginTop: "0.5rem" }}>
                {Object.entries(comparison.comparisons).slice(0, 10).map(([statKey, comp]) => (
                  <div key={statKey} style={{ fontSize: "0.85rem" }}>
                    <div style={{ color: "#86efac", fontWeight: 600 }}>
                      🏆 Best: {comp.best?.player_name} ({comp.best?.value?.toFixed(1)})
                    </div>
                    <div style={{ color: "#fca5a5", marginTop: "0.25rem" }}>
                      ⚠️ Worst: {comp.worst?.player_name} ({comp.worst?.value?.toFixed(1)})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}



