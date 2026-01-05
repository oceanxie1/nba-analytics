import { useState } from "react";
import { safeFetch } from "../utils/api";
import { useStatus } from "../utils/hooks";

export default function TeamComparisonView() {
  const [teams, setTeams] = useState([]);
  const [status, statusKind, setStatus] = useStatus();
  const [teamIds, setTeamIds] = useState("");
  const [season, setSeason] = useState("2023-24");
  const [comparison, setComparison] = useState(null);
  const [comparisonStatus, comparisonStatusKind, setComparisonStatus] = useStatus();

  const loadTeams = async () => {
    setStatus("Loading teams...");
    try {
      const res = await safeFetch("/teams?limit=100");
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

  const loadComparison = async () => {
    if (!teamIds.trim()) {
      setComparisonStatus("Enter team IDs (comma-separated).", "error");
      setComparison(null);
      return;
    }
    
    // Validate team IDs
    const ids = teamIds.split(",").map(id => id.trim()).filter(id => id);
    if (ids.length < 2) {
      setComparisonStatus("Enter at least 2 team IDs.", "error");
      setComparison(null);
      return;
    }
    if (ids.length > 10) {
      setComparisonStatus("Maximum 10 teams can be compared.", "error");
      setComparison(null);
      return;
    }

    setComparisonStatus("Loading comparison...");
    setComparison(null);
    try {
      const idsParam = ids.join(",");
      const seasonParam = season.trim() || "2023-24";
      const res = await safeFetch(`/teams/compare?team_ids=${encodeURIComponent(idsParam)}&season=${encodeURIComponent(seasonParam)}`);
      if (res.ok) {
        setComparison(res.data);
        setComparisonStatus(`Loaded comparison for ${res.data.teams.length} teams.`, "success");
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
  const getStatClass = (statKey, teamIndex, value) => {
    if (!comparison?.comparisons || value == null) return "";
    const comp = comparison.comparisons[statKey];
    if (!comp) return "";
    // Compare with tolerance for floating point values
    const tolerance = 0.01;
    const isBest = comp.best?.team_index === teamIndex && 
                   Math.abs((comp.best?.value || 0) - (value || 0)) < tolerance;
    const isWorst = comp.worst?.team_index === teamIndex && 
                    Math.abs((comp.worst?.value || 0) - (value || 0)) < tolerance;
    if (isBest) return "best";
    if (isWorst) return "worst";
    return "";
  };

  return (
    <section className="view is-visible">
      <div className="card">
        <div className="card-header">
          <h2>Team List (Reference)</h2>
          <button type="button" className="btn" onClick={loadTeams}>
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
              {teams.slice(0, 50).map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.abbreviation}</td>
                  <td>{t.name}</td>
                  <td>{t.city || "-"}</td>
                  <td>{t.conference || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {teams.length > 50 && (
          <p className="hint" style={{ marginTop: "0.5rem" }}>
            Showing first 50 of {teams.length} teams
          </p>
        )}
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <h2>Team Comparison</h2>
          <div className="controls-row">
            <label>
              Team IDs (comma-separated)
              <input
                type="text"
                value={teamIds}
                onChange={(e) => setTeamIds(e.target.value)}
                placeholder="e.g. 1,2"
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
              Compare Teams
            </button>
          </div>
        </div>
        <div className={`status-bar ${comparisonStatusKind}`}>{comparisonStatus}</div>
        <p className="hint" style={{ marginTop: "0.5rem" }}>
          Enter 2-10 team IDs separated by commas. Best stats are highlighted in green, worst in red.
        </p>
      </div>

      {comparison && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <div className="card-header">
            <h2>Comparison Results - {comparison.season}</h2>
          </div>
          
          {/* Record */}
          <div style={{ marginTop: "1.5rem" }}>
            <h3>Record</h3>
            <div className="table-container" style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Team</th>
                    <th>Games</th>
                    <th>Wins</th>
                    <th>Losses</th>
                    <th>Win %</th>
                    <th>Home (W-L)</th>
                    <th>Away (W-L)</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.teams.map((team, idx) => (
                    <tr key={team.team_id}>
                      <td style={{ fontWeight: 600 }}>{team.team_name}</td>
                      <td>{team.games_played}</td>
                      <td className={getStatClass("record_wins", idx, team.record?.wins)}>
                        {team.record?.wins || "-"}
                      </td>
                      <td>{team.record?.losses || "-"}</td>
                      <td className={getStatClass("record_win_percentage", idx, team.record?.win_percentage)}>
                        {team.record?.win_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td>
                        {team.record?.home ? `${team.record.home.wins}-${team.record.home.losses}` : "-"}
                      </td>
                      <td>
                        {team.record?.away ? `${team.record.away.wins}-${team.record.away.losses}` : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Per-Game Stats */}
          <div style={{ marginTop: "2rem" }}>
            <h3>Per-Game Statistics</h3>
            <div className="table-container" style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Team</th>
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
                  {comparison.teams.map((team, idx) => (
                    <tr key={team.team_id}>
                      <td style={{ fontWeight: 600 }}>{team.team_name}</td>
                      <td className={getStatClass("per_game_points", idx, team.per_game?.points)}>
                        {team.per_game?.points?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_rebounds", idx, team.per_game?.rebounds)}>
                        {team.per_game?.rebounds?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_assists", idx, team.per_game?.assists)}>
                        {team.per_game?.assists?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_steals", idx, team.per_game?.steals)}>
                        {team.per_game?.steals?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_blocks", idx, team.per_game?.blocks)}>
                        {team.per_game?.blocks?.toFixed(1) || "-"}
                      </td>
                      <td className={getStatClass("per_game_turnovers", idx, team.per_game?.turnovers)}>
                        {team.per_game?.turnovers?.toFixed(1) || "-"}
                      </td>
                      <td>{team.per_game?.minutes?.toFixed(1) || "-"}</td>
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
                    <th>Team</th>
                    <th>FG%</th>
                    <th>3P%</th>
                    <th>FT%</th>
                    <th>eFG%</th>
                    <th>TS%</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.teams.map((team, idx) => (
                    <tr key={team.team_id}>
                      <td style={{ fontWeight: 600 }}>{team.team_name}</td>
                      <td className={getStatClass("shooting_field_goal_percentage", idx, team.shooting_percentages?.field_goal_percentage)}>
                        {team.shooting_percentages?.field_goal_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_three_point_percentage", idx, team.shooting_percentages?.three_point_percentage)}>
                        {team.shooting_percentages?.three_point_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_free_throw_percentage", idx, team.shooting_percentages?.free_throw_percentage)}>
                        {team.shooting_percentages?.free_throw_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_effective_field_goal_percentage", idx, team.shooting_percentages?.effective_field_goal_percentage)}>
                        {team.shooting_percentages?.effective_field_goal_percentage?.toFixed(1) || "-"}%
                      </td>
                      <td className={getStatClass("shooting_true_shooting_percentage", idx, team.shooting_percentages?.true_shooting_percentage)}>
                        {team.shooting_percentages?.true_shooting_percentage?.toFixed(1) || "-"}%
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
                      🏆 Best: {comp.best?.team_name} ({comp.best?.value?.toFixed(1)})
                    </div>
                    <div style={{ color: "#fca5a5", marginTop: "0.25rem" }}>
                      ⚠️ Worst: {comp.worst?.team_name} ({comp.worst?.value?.toFixed(1)})
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

