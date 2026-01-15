"""Feature engineering for game outcome prediction."""
from typing import Dict
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, distinct
from app.models import Game, Team


def calculate_team_rolling_stats(
    db: Session, team_id: int, game_date: date, season: str, window: int = 10
) -> Dict:
    """Calculate rolling statistics for a team over the last N games.
    
    Args:
        db: Database session
        team_id: Team ID
        game_date: Date of the game
        season: Season string
        window: Number of games to look back
    
    Returns:
        Dictionary with rolling stats (off_rating, def_rating, net_rating, pace, etc.)
    """
    from datetime import date as date_class
    today = date_class.today()
    
    # Determine which season to query for historical data
    season_to_query = season
    if game_date > today:
        # If predicting a future game, use the most recent season with data
        latest_season_row = db.query(Game.season).filter(
            Game.home_score.isnot(None)
        ).order_by(Game.game_date.desc()).first()
        if latest_season_row:
            season_to_query = latest_season_row[0]
        else:
            season_to_query = season
    else:
        # For past/present games, check if the specified season exists
        season_exists = db.query(Game.id).filter(Game.season == season).first()
        if not season_exists:
            latest_season_row = db.query(Game.season).filter(
                Game.home_score.isnot(None)
            ).order_by(Game.game_date.desc()).first()
            if latest_season_row:
                season_to_query = latest_season_row[0]
    
    previous_games = db.query(Game).filter(
        and_(
            or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
            Game.season == season_to_query,
            Game.game_date < game_date,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        )
    ).order_by(Game.game_date.desc()).limit(window).all()
    
    if not previous_games:
        return {
            "off_rating": 100.0,
            "def_rating": 100.0,
            "net_rating": 0.0,
            "pace": 100.0,
            "win_pct": 0.5,
            "ppg": 100.0,
            "ppg_allowed": 100.0
        }
    
    # Calculate stats
    points_for = 0
    points_against = 0
    wins = 0
    total_possessions = 0
    
    for game in previous_games:
        is_home = game.home_team_id == team_id
        team_score = game.home_score if is_home else game.away_score
        opp_score = game.away_score if is_home else game.home_score
        
        points_for += team_score
        points_against += opp_score
        
        if team_score > opp_score:
            wins += 1
        
        # Estimate possessions (simplified)
        total_possessions += (team_score + opp_score) / 2
    
    games_count = len(previous_games)
    avg_points_for = points_for / games_count if games_count > 0 else 100.0
    avg_points_against = points_against / games_count if games_count > 0 else 100.0
    win_pct = wins / games_count if games_count > 0 else 0.5
    avg_possessions = total_possessions / games_count if games_count > 0 else 100.0
    
    # Calculate ratings (points per 100 possessions)
    off_rating = (avg_points_for / avg_possessions * 100) if avg_possessions > 0 else 100.0
    def_rating = (avg_points_against / avg_possessions * 100) if avg_possessions > 0 else 100.0
    net_rating = off_rating - def_rating
    
    return {
        "off_rating": round(off_rating, 2),
        "def_rating": round(def_rating, 2),
        "net_rating": round(net_rating, 2),
        "pace": round(avg_possessions, 2),
        "win_pct": round(win_pct, 3),
        "ppg": round(avg_points_for, 2),
        "ppg_allowed": round(avg_points_against, 2)
    }


def calculate_recent_form(
    db: Session, team_id: int, game_date: date, season: str, window: int = 5
) -> Dict:
    """Calculate recent form (wins/losses) for a team.
    
    Args:
        db: Database session
        team_id: Team ID
        game_date: Date of the game
        season: Season string
        window: Number of recent games to consider
    
    Returns:
        Dictionary with wins, losses, and win_streak
    """
    from datetime import date as date_class
    today = date_class.today()
    
    season_to_query = season
    if game_date > today:
        latest_season_row = db.query(Game.season).filter(
            Game.home_score.isnot(None)
        ).order_by(Game.game_date.desc()).first()
        if latest_season_row:
            season_to_query = latest_season_row[0]
        else:
            season_to_query = season
    else:
        season_exists = db.query(Game.id).filter(Game.season == season).first()
        if not season_exists:
            latest_season_row = db.query(Game.season).filter(
                Game.home_score.isnot(None)
            ).order_by(Game.game_date.desc()).first()
            if latest_season_row:
                season_to_query = latest_season_row[0]
    
    recent_games = db.query(Game).filter(
        and_(
            or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
            Game.season == season_to_query,
            Game.game_date < game_date,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        )
    ).order_by(Game.game_date.desc()).limit(window).all()
    
    wins = 0
    losses = 0
    win_streak = 0
    
    for game in recent_games:
        is_home = game.home_team_id == team_id
        team_score = game.home_score if is_home else game.away_score
        opp_score = game.away_score if is_home else game.home_score
        
        if team_score > opp_score:
            wins += 1
            if win_streak == losses:  # Start of streak
                win_streak = 1
            else:
                win_streak += 1
        else:
            losses += 1
            if win_streak > 0:
                win_streak = 0
    
    return {
        "wins": wins,
        "losses": losses,
        "win_streak": max(win_streak, 0)
    }


def calculate_head_to_head(
    db: Session, team1_id: int, team2_id: int, game_date: date, season: str
) -> Dict:
    """Calculate head-to-head record between two teams.
    
    Args:
        db: Database session
        team1_id: First team ID (typically home team)
        team2_id: Second team ID (typically away team)
        game_date: Date of the game
        season: Season string
    
    Returns:
        Dictionary with team1_wins, team2_wins, and avg_point_diff
    """
    from datetime import date as date_class
    from sqlalchemy import distinct
    today = date_class.today()
    
    query = db.query(Game).filter(
        and_(
            or_(
                and_(Game.home_team_id == team1_id, Game.away_team_id == team2_id),
                and_(Game.home_team_id == team2_id, Game.away_team_id == team1_id)
            ),
            Game.game_date < game_date,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        )
    )
    
    existing_seasons = {s[0] for s in db.query(distinct(Game.season)).filter(
        Game.home_score.isnot(None)
    ).all()}
    latest_season_row = db.query(Game.season).filter(
        Game.home_score.isnot(None)
    ).order_by(Game.game_date.desc()).first()
    latest_season = latest_season_row[0] if latest_season_row else None
    
    if season in existing_seasons:
        latest_game_date = db.query(Game.game_date).filter(
            Game.home_score.isnot(None)
        ).order_by(Game.game_date.desc()).first()
        if latest_game_date and (game_date - latest_game_date[0]).days > 365:
            if latest_season:
                query = query.filter(Game.season == latest_season)
        else:
            query = query.filter(Game.season == season)
    else:
        if latest_season:
            query = query.filter(Game.season == latest_season)
    
    h2h_games = query.all()
    
    if not h2h_games:
        return {
            "team1_wins": 0,
            "team2_wins": 0,
            "avg_point_diff": 0.0
        }
    
    team1_wins = 0
    team2_wins = 0
    point_diffs = []
    
    for game in h2h_games:
        is_team1_home = game.home_team_id == team1_id
        team1_score = game.home_score if is_team1_home else game.away_score
        team2_score = game.away_score if is_team1_home else game.home_score
        
        if team1_score is not None and team2_score is not None:
            point_diff = team1_score - team2_score
            point_diffs.append(point_diff)
            
            if point_diff > 0:
                team1_wins += 1
            else:
                team2_wins += 1
    
    avg_point_diff = sum(point_diffs) / len(point_diffs) if point_diffs else 0.0
    
    return {
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "avg_point_diff": round(avg_point_diff, 1)
    }


def calculate_rest_days(
    db: Session, team_id: int, game_date: date, season: str
) -> int:
    """Calculate rest days for a team before a game.
    
    Args:
        db: Database session
        team_id: Team ID
        game_date: Date of the game
        season: Season string
    
    Returns:
        Number of rest days (0 = back-to-back, 1 = 1 day rest, etc.)
    """
    from datetime import date as date_class
    from sqlalchemy import distinct
    today = date_class.today()
    
    query = db.query(Game).filter(
        and_(
            or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
            Game.game_date < game_date,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        )
    )
    
    existing_seasons = {s[0] for s in db.query(distinct(Game.season)).filter(
        Game.home_score.isnot(None)
    ).all()}
    latest_season_row = db.query(Game.season).filter(
        Game.home_score.isnot(None)
    ).order_by(Game.game_date.desc()).first()
    latest_season = latest_season_row[0] if latest_season_row else None
    
    if season in existing_seasons:
        latest_game_date = db.query(Game.game_date).filter(
            Game.home_score.isnot(None)
        ).order_by(Game.game_date.desc()).first()
        if latest_game_date and (game_date - latest_game_date[0]).days > 365:
            if latest_season:
                query = query.filter(Game.season == latest_season)
        else:
            query = query.filter(Game.season == season)
    else:
        if latest_season:
            query = query.filter(Game.season == latest_season)
    
    previous_game = query.order_by(Game.game_date.desc()).first()
    
    if not previous_game:
        return 3  # Default to 3 days if no previous game (start of season)
    
    rest_days = (game_date - previous_game.game_date).days - 1
    return max(0, rest_days)


def build_game_features(
    db: Session, game: Game, home_team_id: int, away_team_id: int
) -> Dict:
    """Build feature vector for a game prediction.
    
    Args:
        db: Database session
        game: Game object
        home_team_id: Home team ID
        away_team_id: Away team ID
    
    Returns:
        Dictionary with all features for the game
    """
    # Home team rolling stats (last 10 games)
    home_rolling = calculate_team_rolling_stats(
        db, home_team_id, game.game_date, game.season, window=10
    )
    
    # Away team rolling stats (last 10 games)
    away_rolling = calculate_team_rolling_stats(
        db, away_team_id, game.game_date, game.season, window=10
    )
    
    # Recent form (last 5 games)
    home_form = calculate_recent_form(
        db, home_team_id, game.game_date, game.season, window=5
    )
    
    away_form = calculate_recent_form(
        db, away_team_id, game.game_date, game.season, window=5
    )
    
    # Head-to-head record
    h2h = calculate_head_to_head(
        db, home_team_id, away_team_id, game.game_date, game.season
    )
    
    # Rest days
    home_rest_days = calculate_rest_days(db, home_team_id, game.game_date, game.season)
    away_rest_days = calculate_rest_days(db, away_team_id, game.game_date, game.season)
    
    # Home/away records for the season
    # Use the same season fallback logic as other functions
    from datetime import date as date_class
    today = date_class.today()
    season_to_query = game.season
    
    # Check if season exists and use appropriate filter
    existing_seasons = {s[0] for s in db.query(distinct(Game.season)).filter(
        Game.home_score.isnot(None)
    ).all()}
    latest_season_row = db.query(Game.season).filter(
        Game.home_score.isnot(None)
    ).order_by(Game.game_date.desc()).first()
    latest_season = latest_season_row[0] if latest_season_row else None
    
    if game.season not in existing_seasons:
        if latest_season:
            season_to_query = latest_season
    elif game.game_date > today:
        # For future games, check if date is far in future
        latest_game_date = db.query(Game.game_date).filter(
            Game.home_score.isnot(None)
        ).order_by(Game.game_date.desc()).first()
        if latest_game_date and (game.game_date - latest_game_date[0]).days > 365:
            if latest_season:
                season_to_query = latest_season
    
    home_team = db.query(Team).filter(Team.id == home_team_id).first()
    away_team = db.query(Team).filter(Team.id == away_team_id).first()
    
    # Calculate home team's home record
    home_home_games = db.query(Game).filter(
        and_(
            Game.home_team_id == home_team_id,
            Game.season == season_to_query,
            Game.game_date < game.game_date,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        )
    ).all()
    
    home_home_wins = sum(1 for g in home_home_games if g.home_score > g.away_score)
    home_home_win_pct = home_home_wins / len(home_home_games) if home_home_games else 0.5
    
    # Calculate away team's away record
    away_away_games = db.query(Game).filter(
        and_(
            Game.away_team_id == away_team_id,
            Game.season == season_to_query,
            Game.game_date < game.game_date,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        )
    ).all()
    
    away_away_wins = sum(1 for g in away_away_games if g.away_score > g.home_score)
    away_away_win_pct = away_away_wins / len(away_away_games) if away_away_games else 0.5
    
    # Build feature dictionary
    features = {
        # Home team rolling stats
        "home_off_rating": home_rolling["off_rating"],
        "home_def_rating": home_rolling["def_rating"],
        "home_net_rating": home_rolling["net_rating"],
        "home_pace": home_rolling["pace"],
        "home_win_pct_last_10": home_rolling["win_pct"],
        "home_ppg_last_10": home_rolling["ppg"],
        "home_ppg_allowed_last_10": home_rolling["ppg_allowed"],
        
        # Away team rolling stats
        "away_off_rating": away_rolling["off_rating"],
        "away_def_rating": away_rolling["def_rating"],
        "away_net_rating": away_rolling["net_rating"],
        "away_pace": away_rolling["pace"],
        "away_win_pct_last_10": away_rolling["win_pct"],
        "away_ppg_last_10": away_rolling["ppg"],
        "away_ppg_allowed_last_10": away_rolling["ppg_allowed"],
        
        # Recent form
        "home_wins_last_5": home_form["wins"],
        "home_losses_last_5": home_form["losses"],
        "home_win_streak": home_form["win_streak"],
        "away_wins_last_5": away_form["wins"],
        "away_losses_last_5": away_form["losses"],
        "away_win_streak": away_form["win_streak"],
        
        # Head-to-head
        "h2h_home_wins": h2h["team1_wins"],
        "h2h_away_wins": h2h["team2_wins"],
        "h2h_avg_point_diff": h2h["avg_point_diff"],
        
        # Rest days
        "home_rest_days": home_rest_days,
        "away_rest_days": away_rest_days,
        "home_back_to_back": 1 if home_rest_days == 0 else 0,
        "away_back_to_back": 1 if away_rest_days == 0 else 0,
        
        # Home/away records
        "home_home_win_pct": home_home_win_pct,
        "away_away_win_pct": away_away_win_pct,
        
        # Differential features
        "net_rating_diff": home_rolling["net_rating"] - away_rolling["net_rating"],
        "win_pct_diff": home_rolling["win_pct"] - away_rolling["win_pct"],
        "rest_days_diff": home_rest_days - away_rest_days
    }
    
    return features



