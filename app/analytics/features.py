"""Feature engineering for NBA player analytics."""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models import BoxScore, Game, Player


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is 0."""
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def calculate_true_shooting_percentage(
    points: int, fga: int, fta: int
) -> Optional[float]:
    """Calculate True Shooting Percentage (TS%).
    
    TS% = PTS / (2 * (FGA + 0.44 * FTA))
    """
    if fga == 0 and fta == 0:
        return None
    denominator = 2 * (fga + 0.44 * fta)
    if denominator == 0:
        return None
    return (points / denominator) * 100


def calculate_effective_field_goal_percentage(fgm: int, fg3m: int, fga: int) -> Optional[float]:
    """Calculate Effective Field Goal Percentage (eFG%).
    
    eFG% = (FGM + 0.5 * 3PM) / FGA
    """
    if fga == 0:
        return None
    return ((fgm + 0.5 * fg3m) / fga) * 100


def calculate_usage_rate(
    fga: int, fta: int, tov: int, minutes: float, team_fga: int, team_fta: int, team_tov: int, team_minutes: float
) -> Optional[float]:
    """Calculate Usage Rate (USG%).
    
    USG% = 100 * ((FGA + 0.44 * FTA + TOV) * (Team Minutes / 5)) / (Minutes * (Team FGA + 0.44 * Team FTA + Team TOV))
    
    Simplified version when team stats aren't available:
    USG% = (FGA + 0.44 * FTA + TOV) / (Minutes * 2) * 100
    """
    if minutes == 0 or minutes is None:
        return None
    
    if team_fga > 0:  # Full calculation with team stats
        player_possessions = fga + 0.44 * fta + tov
        team_possessions = team_fga + 0.44 * team_fta + team_tov
        if team_possessions == 0:
            return None
        team_minutes_total = team_minutes / 5  # Convert to team minutes
        usage = 100 * ((player_possessions * team_minutes_total) / (minutes * team_possessions))
    else:  # Simplified calculation
        possessions = fga + 0.44 * fta + tov
        usage = (possessions / (minutes * 2)) * 100
    
    return usage


def calculate_player_efficiency_rating(
    points: int, fgm: int, fga: int, ftm: int, fta: int,
    rebounds: int, assists: int, steals: int, blocks: int,
    turnovers: int, personal_fouls: int, minutes: float
) -> Optional[float]:
    """Calculate Player Efficiency Rating (PER).
    
    Simplified PER formula:
    PER = (1 / Minutes) * (
        Points + (FGM * 0.5) - (FGA - FGM) * 0.5 - (FTA - FTM) * 0.5 +
        Rebounds * 1.25 + Assists * 1.5 + Steals * 2.0 + Blocks * 2.0 -
        Turnovers * 0.5 - Personal Fouls * 0.25
    )
    """
    if minutes == 0 or minutes is None:
        return None
    
    per = (
        points +
        (fgm * 0.5) -
        ((fga - fgm) * 0.5) -
        ((fta - ftm) * 0.5) +
        (rebounds * 1.25) +
        (assists * 1.5) +
        (steals * 2.0) +
        (blocks * 2.0) -
        (turnovers * 0.5) -
        (personal_fouls * 0.25)
    ) / minutes
    
    return per


def get_player_box_scores(
    db: Session, player_id: int, season: Optional[str] = None, limit: Optional[int] = None
) -> List[BoxScore]:
    """Get box scores for a player, optionally filtered by season."""
    query = db.query(BoxScore).join(Game).filter(BoxScore.player_id == player_id)
    
    if season:
        query = query.filter(Game.season == season)
    
    query = query.order_by(desc(Game.game_date))
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def calculate_season_features(
    db: Session, player_id: int, season: str
) -> Dict:
    """Calculate comprehensive season features for a player."""
    box_scores = get_player_box_scores(db, player_id, season=season)
    
    if not box_scores:
        return {
            "error": f"No games found for player {player_id} in season {season}"
        }
    
    # Aggregate totals
    games_played = len(box_scores)
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
    ts_percentage = calculate_true_shooting_percentage(total_points, total_fga, total_fta)
    efg_percentage = calculate_effective_field_goal_percentage(total_fgm, total_fg3m, total_fga)
    
    # Simplified PER (without team stats)
    per = calculate_player_efficiency_rating(
        total_points, total_fgm, total_fga, total_ftm, total_fta,
        total_rebounds, total_assists, total_steals, total_blocks,
        total_turnovers, total_personal_fouls, total_minutes
    )
    
    # Usage rate (simplified, without team stats)
    usage_rate = calculate_usage_rate(
        total_fga, total_fta, total_turnovers, total_minutes,
        0, 0, 0, 0  # Team stats not available
    )
    
    return {
        "season": season,
        "games_played": games_played,
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
        "advanced_stats": {
            "player_efficiency_rating": round(per, 2) if per is not None else None,
            "usage_rate": round(usage_rate, 1) if usage_rate is not None else None,
        }
    }


def calculate_rolling_averages(
    db: Session, player_id: int, season: Optional[str] = None, window: int = 5
) -> List[Dict]:
    """Calculate rolling averages for a player's last N games."""
    box_scores = get_player_box_scores(db, player_id, season=season, limit=window * 2)  # Get more for context
    
    if len(box_scores) < window:
        return []
    
    rolling_stats = []
    
    for i in range(len(box_scores) - window + 1):
        window_scores = box_scores[i:i + window]
        
        # Aggregate window stats
        total_points = sum(bs.points or 0 for bs in window_scores)
        total_rebounds = sum(bs.rebounds or 0 for bs in window_scores)
        total_assists = sum(bs.assists or 0 for bs in window_scores)
        total_minutes = sum(bs.minutes or 0 for bs in window_scores)
        
        rolling_stats.append({
            "game_index": i + window - 1,
            "games_in_window": window,
            "avg_points": round(total_points / window, 1),
            "avg_rebounds": round(total_rebounds / window, 1),
            "avg_assists": round(total_assists / window, 1),
            "avg_minutes": round(total_minutes / window, 1),
        })
    
    return rolling_stats


def calculate_career_features(
    db: Session, player_id: int
) -> Dict:
    """Calculate career averages for a player across all seasons."""
    box_scores = get_player_box_scores(db, player_id)
    
    if not box_scores:
        return {
            "error": f"No games found for player {player_id}"
        }
    
    # Get unique seasons
    seasons = set()
    for bs in box_scores:
        game = db.query(Game).filter(Game.id == bs.game_id).first()
        if game:
            seasons.add(game.season)
    
    # Aggregate across all seasons
    games_played = len(box_scores)
    total_minutes = sum(bs.minutes or 0 for bs in box_scores)
    total_points = sum(bs.points or 0 for bs in box_scores)
    total_rebounds = sum(bs.rebounds or 0 for bs in box_scores)
    total_assists = sum(bs.assists or 0 for bs in box_scores)
    total_steals = sum(bs.steals or 0 for bs in box_scores)
    total_blocks = sum(bs.blocks or 0 for bs in box_scores)
    
    total_fgm = sum(bs.field_goals_made or 0 for bs in box_scores)
    total_fga = sum(bs.field_goals_attempted or 0 for bs in box_scores)
    total_fg3m = sum(bs.three_pointers_made or 0 for bs in box_scores)
    total_fg3a = sum(bs.three_pointers_attempted or 0 for bs in box_scores)
    total_ftm = sum(bs.free_throws_made or 0 for bs in box_scores)
    total_fta = sum(bs.free_throws_attempted or 0 for bs in box_scores)
    
    # Career averages
    minutes_per_game = safe_divide(total_minutes, games_played)
    points_per_game = safe_divide(total_points, games_played)
    rebounds_per_game = safe_divide(total_rebounds, games_played)
    assists_per_game = safe_divide(total_assists, games_played)
    steals_per_game = safe_divide(total_steals, games_played)
    blocks_per_game = safe_divide(total_blocks, games_played)
    
    fg_percentage = safe_divide(total_fgm, total_fga) * 100 if total_fga > 0 else None
    fg3_percentage = safe_divide(total_fg3m, total_fg3a) * 100 if total_fg3a > 0 else None
    ft_percentage = safe_divide(total_ftm, total_fta) * 100 if total_fta > 0 else None
    
    return {
        "games_played": games_played,
        "seasons": sorted(list(seasons)),
        "career_averages": {
            "minutes": round(minutes_per_game, 1),
            "points": round(points_per_game, 1),
            "rebounds": round(rebounds_per_game, 1),
            "assists": round(assists_per_game, 1),
            "steals": round(steals_per_game, 1),
            "blocks": round(blocks_per_game, 1),
        },
        "career_shooting": {
            "field_goal_percentage": round(fg_percentage, 1) if fg_percentage is not None else None,
            "three_point_percentage": round(fg3_percentage, 1) if fg3_percentage is not None else None,
            "free_throw_percentage": round(ft_percentage, 1) if ft_percentage is not None else None,
        }
    }

