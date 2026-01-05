"""Feature engineering for NBA team analytics."""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models import BoxScore, Game, Team, Player


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is 0."""
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def calculate_possessions(fga: int, fta: int, tov: int, orb: int = 0) -> float:
    """Calculate possessions using the standard formula.
    
    Formula: Possessions = FGA - ORB + TOV + 0.44 * FTA
    
    Note: Without offensive rebounds, we use a simplified formula:
    Possessions ≈ FGA + 0.44 * FTA + TOV
    """
    return fga + 0.44 * fta + tov


def calculate_offensive_rating(points: int, possessions: float) -> Optional[float]:
    """Calculate Offensive Rating (points per 100 possessions)."""
    if possessions == 0:
        return None
    return (points / possessions) * 100


def calculate_defensive_rating(opponent_points: int, opponent_possessions: float) -> Optional[float]:
    """Calculate Defensive Rating (opponent points per 100 possessions)."""
    if opponent_possessions == 0:
        return None
    return (opponent_points / opponent_possessions) * 100


def calculate_turnover_percentage(tov: int, fga: int, fta: int) -> Optional[float]:
    """Calculate Turnover Percentage (TOV%).
    
    Formula: TOV% = (TOV / (FGA + 0.44 * FTA + TOV)) * 100
    """
    possessions = fga + 0.44 * fta + tov
    if possessions == 0:
        return None
    return (tov / possessions) * 100


def calculate_fta_rate(fta: int, fga: int) -> Optional[float]:
    """Calculate Free Throw Attempt Rate (FTA Rate).
    
    Formula: FTA Rate = FTA / FGA
    """
    if fga == 0:
        return None
    return (fta / fga) * 100


def get_team_games(
    db: Session, team_id: int, season: Optional[str] = None
) -> List[Game]:
    """Get all games for a team, optionally filtered by season."""
    query = db.query(Game).filter(
        or_(
            Game.home_team_id == team_id,
            Game.away_team_id == team_id
        )
    )
    
    if season:
        query = query.filter(Game.season == season)
    
    query = query.order_by(Game.game_date)
    
    return query.all()


def get_team_box_scores(
    db: Session, team_id: int, season: Optional[str] = None
) -> List[BoxScore]:
    """Get all box scores for players on a team, optionally filtered by season."""
    query = db.query(BoxScore).join(Player).join(Game).filter(
        Player.team_id == team_id
    )
    
    if season:
        query = query.filter(Game.season == season)
    
    return query.all()


def calculate_team_season_stats(
    db: Session, team_id: int, season: str
) -> Dict:
    """Calculate comprehensive season stats for a team."""
    # Get all games for this team in this season
    games = get_team_games(db, team_id, season=season)
    
    if not games:
        return {
            "error": f"No games found for team {team_id} in season {season}"
        }
    
    # Get all box scores for players on this team in this season
    box_scores = get_team_box_scores(db, team_id, season=season)
    
    # Calculate win/loss record
    wins = 0
    losses = 0
    home_wins = 0
    home_losses = 0
    away_wins = 0
    away_losses = 0
    
    for game in games:
        is_home = game.home_team_id == team_id
        team_score = game.home_score if is_home else game.away_score
        opponent_score = game.away_score if is_home else game.home_score
        
        if team_score is not None and opponent_score is not None:
            if team_score > opponent_score:
                wins += 1
                if is_home:
                    home_wins += 1
                else:
                    away_wins += 1
            else:
                losses += 1
                if is_home:
                    home_losses += 1
                else:
                    away_losses += 1
    
    games_played = wins + losses
    win_percentage = safe_divide(wins, games_played) * 100 if games_played > 0 else 0
    
    # Aggregate team totals from box scores
    total_minutes = sum(bs.minutes or 0 for bs in box_scores)
    total_points = sum(bs.points or 0 for bs in box_scores)
    total_rebounds = sum(bs.rebounds or 0 for bs in box_scores)
    total_assists = sum(bs.assists or 0 for bs in box_scores)
    total_steals = sum(bs.steals or 0 for bs in box_scores)
    total_blocks = sum(bs.blocks or 0 for bs in box_scores)
    total_turnovers = sum(bs.turnovers or 0 for bs in box_scores)
    total_personal_fouls = sum(bs.personal_fouls or 0 for bs in box_scores)
    
    total_fgm = sum(bs.field_goals_made or 0 for bs in box_scores)
    total_fga = sum(bs.field_goals_attempted or 0 for bs in box_scores)
    total_fg3m = sum(bs.three_pointers_made or 0 for bs in box_scores)
    total_fg3a = sum(bs.three_pointers_attempted or 0 for bs in box_scores)
    total_ftm = sum(bs.free_throws_made or 0 for bs in box_scores)
    total_fta = sum(bs.free_throws_attempted or 0 for bs in box_scores)
    total_plus_minus = sum(bs.plus_minus or 0 for bs in box_scores)
    
    # Per-game averages
    minutes_per_game = safe_divide(total_minutes, games_played)
    points_per_game = safe_divide(total_points, games_played)
    rebounds_per_game = safe_divide(total_rebounds, games_played)
    assists_per_game = safe_divide(total_assists, games_played)
    steals_per_game = safe_divide(total_steals, games_played)
    blocks_per_game = safe_divide(total_blocks, games_played)
    turnovers_per_game = safe_divide(total_turnovers, games_played)
    personal_fouls_per_game = safe_divide(total_personal_fouls, games_played)
    plus_minus_per_game = safe_divide(total_plus_minus, games_played)
    
    # Shooting percentages
    fg_percentage = safe_divide(total_fgm, total_fga) * 100 if total_fga > 0 else None
    fg3_percentage = safe_divide(total_fg3m, total_fg3a) * 100 if total_fg3a > 0 else None
    ft_percentage = safe_divide(total_ftm, total_fta) * 100 if total_fta > 0 else None
    
    # Advanced stats
    from app.analytics.features import (
        calculate_true_shooting_percentage,
        calculate_effective_field_goal_percentage
    )
    
    ts_percentage = calculate_true_shooting_percentage(total_points, total_fga, total_fta)
    efg_percentage = calculate_effective_field_goal_percentage(total_fgm, total_fg3m, total_fga)
    
    # Calculate opponent stats for defensive rating
    opponent_points = 0
    opponent_fga = 0
    opponent_fta = 0
    opponent_tov = 0
    
    for game in games:
        is_home = game.home_team_id == team_id
        opponent_id = game.away_team_id if is_home else game.home_team_id
        
        # Get opponent box scores for this game
        opponent_box_scores = db.query(BoxScore).join(Player).filter(
            BoxScore.game_id == game.id,
            Player.team_id == opponent_id
        ).all()
        
        for bs in opponent_box_scores:
            opponent_points += bs.points or 0
            opponent_fga += bs.field_goals_attempted or 0
            opponent_fta += bs.free_throws_attempted or 0
            opponent_tov += bs.turnovers or 0
    
    # Calculate advanced metrics
    # Pace (possessions per game)
    total_possessions = calculate_possessions(total_fga, total_fta, total_turnovers)
    pace = safe_divide(total_possessions, games_played) if games_played > 0 else None
    
    # Offensive Rating
    offensive_rating = calculate_offensive_rating(total_points, total_possessions)
    
    # Defensive Rating
    opponent_possessions = calculate_possessions(opponent_fga, opponent_fta, opponent_tov)
    defensive_rating = calculate_defensive_rating(opponent_points, opponent_possessions)
    
    # Net Rating
    net_rating = None
    if offensive_rating is not None and defensive_rating is not None:
        net_rating = offensive_rating - defensive_rating
    
    # Four Factors
    # 1. eFG% (already calculated)
    # 2. TOV% (Turnover Percentage)
    tov_percentage = calculate_turnover_percentage(total_turnovers, total_fga, total_fta)
    
    # 3. ORB% (Offensive Rebound Percentage) - Note: We don't have ORB data, so we'll skip this
    # 4. FTA Rate (Free Throw Attempt Rate)
    fta_rate = calculate_fta_rate(total_fta, total_fga)
    
    return {
        "season": season,
        "games_played": games_played,
        "record": {
            "wins": wins,
            "losses": losses,
            "win_percentage": round(win_percentage, 1),
            "home": {
                "wins": home_wins,
                "losses": home_losses
            },
            "away": {
                "wins": away_wins,
                "losses": away_losses
            }
        },
        "totals": {
            "minutes": total_minutes,
            "points": total_points,
            "rebounds": total_rebounds,
            "assists": total_assists,
            "steals": total_steals,
            "blocks": total_blocks,
            "turnovers": total_turnovers,
            "personal_fouls": total_personal_fouls,
            "field_goals_made": total_fgm,
            "field_goals_attempted": total_fga,
            "three_pointers_made": total_fg3m,
            "three_pointers_attempted": total_fg3a,
            "free_throws_made": total_ftm,
            "free_throws_attempted": total_fta,
            "plus_minus": total_plus_minus,
        },
        "per_game": {
            "minutes": round(minutes_per_game, 1),
            "points": round(points_per_game, 1),
            "rebounds": round(rebounds_per_game, 1),
            "assists": round(assists_per_game, 1),
            "steals": round(steals_per_game, 1),
            "blocks": round(blocks_per_game, 1),
            "turnovers": round(turnovers_per_game, 1),
            "personal_fouls": round(personal_fouls_per_game, 1),
            "plus_minus": round(plus_minus_per_game, 1),
        },
        "shooting_percentages": {
            "field_goal_percentage": round(fg_percentage, 1) if fg_percentage is not None else None,
            "three_point_percentage": round(fg3_percentage, 1) if fg3_percentage is not None else None,
            "free_throw_percentage": round(ft_percentage, 1) if ft_percentage is not None else None,
            "effective_field_goal_percentage": round(efg_percentage, 1) if efg_percentage is not None else None,
            "true_shooting_percentage": round(ts_percentage, 1) if ts_percentage is not None else None,
        },
        "advanced_metrics": {
            "pace": round(pace, 1) if pace is not None else None,
            "offensive_rating": round(offensive_rating, 1) if offensive_rating is not None else None,
            "defensive_rating": round(defensive_rating, 1) if defensive_rating is not None else None,
            "net_rating": round(net_rating, 1) if net_rating is not None else None,
        },
        "four_factors": {
            "effective_field_goal_percentage": round(efg_percentage, 1) if efg_percentage is not None else None,
            "turnover_percentage": round(tov_percentage, 1) if tov_percentage is not None else None,
            "free_throw_attempt_rate": round(fta_rate, 1) if fta_rate is not None else None,
            # Note: Offensive rebound percentage requires ORB data which we don't have
        }
    }


def calculate_game_team_stats(
    db: Session, game_id: int, team_id: int
) -> Dict:
    """Calculate team stats for a specific game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        return {"error": f"Game {game_id} not found"}
    
    # Check if team is in this game
    if game.home_team_id != team_id and game.away_team_id != team_id:
        return {"error": f"Team {team_id} is not in game {game_id}"}
    
    # Get all box scores for players on this team in this game
    box_scores = db.query(BoxScore).join(Player).filter(
        BoxScore.game_id == game_id,
        Player.team_id == team_id
    ).all()
    
    if not box_scores:
        return {"error": f"No box scores found for team {team_id} in game {game_id}"}
    
    # Aggregate stats
    total_points = sum(bs.points or 0 for bs in box_scores)
    total_rebounds = sum(bs.rebounds or 0 for bs in box_scores)
    total_assists = sum(bs.assists or 0 for bs in box_scores)
    total_steals = sum(bs.steals or 0 for bs in box_scores)
    total_blocks = sum(bs.blocks or 0 for bs in box_scores)
    total_turnovers = sum(bs.turnovers or 0 for bs in box_scores)
    
    total_fgm = sum(bs.field_goals_made or 0 for bs in box_scores)
    total_fga = sum(bs.field_goals_attempted or 0 for bs in box_scores)
    total_fg3m = sum(bs.three_pointers_made or 0 for bs in box_scores)
    total_fg3a = sum(bs.three_pointers_attempted or 0 for bs in box_scores)
    total_ftm = sum(bs.free_throws_made or 0 for bs in box_scores)
    total_fta = sum(bs.free_throws_attempted or 0 for bs in box_scores)
    
    fg_percentage = safe_divide(total_fgm, total_fga) * 100 if total_fga > 0 else None
    fg3_percentage = safe_divide(total_fg3m, total_fg3a) * 100 if total_fg3a > 0 else None
    ft_percentage = safe_divide(total_ftm, total_fta) * 100 if total_fta > 0 else None
    
    is_home = game.home_team_id == team_id
    team_score = game.home_score if is_home else game.away_score
    opponent_score = game.away_score if is_home else game.home_score
    
    return {
        "game_id": game_id,
        "game_date": game.game_date.isoformat(),
        "is_home": is_home,
        "team_score": team_score,
        "opponent_score": opponent_score,
        "won": team_score is not None and opponent_score is not None and team_score > opponent_score,
        "stats": {
            "points": total_points,
            "rebounds": total_rebounds,
            "assists": total_assists,
            "steals": total_steals,
            "blocks": total_blocks,
            "turnovers": total_turnovers,
            "field_goals_made": total_fgm,
            "field_goals_attempted": total_fga,
            "three_pointers_made": total_fg3m,
            "three_pointers_attempted": total_fg3a,
            "free_throws_made": total_ftm,
            "free_throws_attempted": total_fta,
            "field_goal_percentage": round(fg_percentage, 1) if fg_percentage is not None else None,
            "three_point_percentage": round(fg3_percentage, 1) if fg3_percentage is not None else None,
            "free_throw_percentage": round(ft_percentage, 1) if ft_percentage is not None else None,
        }
    }


def compare_teams(
    db: Session, team_ids: List[int], season: str
) -> Dict:
    """Compare multiple teams side-by-side for a given season.
    
    Returns a dictionary with:
    - season: The season being compared
    - teams: List of team stats for each team
    - comparisons: Highlighted differences (best/worst for each stat)
    """
    if not team_ids or len(team_ids) < 2:
        return {
            "error": "At least 2 team IDs are required for comparison"
        }
    
    if len(team_ids) > 10:
        return {
            "error": "Maximum 10 teams can be compared at once"
        }
    
    teams_data = []
    teams_info = []
    
    # Get team info and stats for each team
    for team_id in team_ids:
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {
                "error": f"Team {team_id} not found"
            }
        
        stats = calculate_team_season_stats(db, team_id, season)
        if "error" in stats:
            return {
                "error": f"Team {team_id} ({team.name}): {stats['error']}"
            }
        
        teams_info.append({
            "team_id": team_id,
            "team_name": team.name,
            "abbreviation": team.abbreviation,
        })
        
        teams_data.append(stats)
    
    # Calculate comparisons (find best/worst for key stats)
    comparisons = {}
    
    # Record stats to compare
    record_stats = ["wins", "win_percentage"]
    for stat in record_stats:
        values = []
        for i, team_stats in enumerate(teams_data):
            if stat == "wins":
                value = team_stats.get("record", {}).get("wins")
            elif stat == "win_percentage":
                value = team_stats.get("record", {}).get("win_percentage")
            if value is not None:
                values.append((i, value))
        
        if values:
            best_idx, best_val = max(values, key=lambda x: x[1])
            worst_idx, worst_val = min(values, key=lambda x: x[1])
            
            comparisons[f"record_{stat}"] = {
                "best": {
                    "team_index": best_idx,
                    "team_id": team_ids[best_idx],
                    "team_name": teams_info[best_idx]["team_name"],
                    "value": best_val
                },
                "worst": {
                    "team_index": worst_idx,
                    "team_id": team_ids[worst_idx],
                    "team_name": teams_info[worst_idx]["team_name"],
                    "value": worst_val
                }
            }
    
    # Per-game stats to compare
    per_game_stats = ["points", "rebounds", "assists", "steals", "blocks", "turnovers"]
    for stat in per_game_stats:
        values = []
        for i, team_stats in enumerate(teams_data):
            value = team_stats.get("per_game", {}).get(stat)
            if value is not None:
                values.append((i, value))
        
        if values:
            # For turnovers, lower is better
            if stat == "turnovers":
                best_idx, best_val = min(values, key=lambda x: x[1])
                worst_idx, worst_val = max(values, key=lambda x: x[1])
            else:
                best_idx, best_val = max(values, key=lambda x: x[1])
                worst_idx, worst_val = min(values, key=lambda x: x[1])
            
            comparisons[f"per_game_{stat}"] = {
                "best": {
                    "team_index": best_idx,
                    "team_id": team_ids[best_idx],
                    "team_name": teams_info[best_idx]["team_name"],
                    "value": best_val
                },
                "worst": {
                    "team_index": worst_idx,
                    "team_id": team_ids[worst_idx],
                    "team_name": teams_info[worst_idx]["team_name"],
                    "value": worst_val
                }
            }
    
    # Shooting percentages to compare
    shooting_stats = ["field_goal_percentage", "three_point_percentage", "free_throw_percentage", 
                      "effective_field_goal_percentage", "true_shooting_percentage"]
    for stat in shooting_stats:
        values = []
        for i, team_stats in enumerate(teams_data):
            value = team_stats.get("shooting_percentages", {}).get(stat)
            if value is not None:
                values.append((i, value))
        
        if values:
            best_idx, best_val = max(values, key=lambda x: x[1])
            worst_idx, worst_val = min(values, key=lambda x: x[1])
            
            comparisons[f"shooting_{stat}"] = {
                "best": {
                    "team_index": best_idx,
                    "team_id": team_ids[best_idx],
                    "team_name": teams_info[best_idx]["team_name"],
                    "value": best_val
                },
                "worst": {
                    "team_index": worst_idx,
                    "team_id": team_ids[worst_idx],
                    "team_name": teams_info[worst_idx]["team_name"],
                    "value": worst_val
                }
            }
    
    # Combine team info with their stats
    teams_comparison = []
    for i, (info, stats) in enumerate(zip(teams_info, teams_data)):
        teams_comparison.append({
            **info,
            "games_played": stats.get("games_played", 0),
            "record": stats.get("record", {}),
            "totals": stats.get("totals", {}),
            "per_game": stats.get("per_game", {}),
            "shooting_percentages": stats.get("shooting_percentages", {}),
        })
    
    return {
        "season": season,
        "teams": teams_comparison,
        "comparisons": comparisons
    }

