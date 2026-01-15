"""Data preparation for game outcome prediction."""
from typing import List, Tuple, Dict, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models import Game
from app.ml.features import build_game_features


def prepare_training_data(
    db: Session,
    train_seasons: List[str],
    test_season: Optional[str] = None,
    min_games_per_team: int = 10
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """Prepare training and test datasets for game outcome prediction.
    
    Args:
        db: Database session
        train_seasons: List of seasons to use for training (e.g., ['2020-21', '2021-22'])
        test_season: Season to use for testing (e.g., '2023-24'). If None, no test set.
        min_games_per_team: Minimum games a team must have played before including their games
    
    Returns:
        Tuple of (train_df, test_df) or (train_df, None) if no test season
        Each DataFrame has columns:
        - All feature columns from build_game_features
        - target: 1 if home team wins, 0 if away team wins
    """
    all_features = []
    all_targets = []
    
    # Process training seasons
    for season in train_seasons:
        games = db.query(Game).filter(
            Game.season == season,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).order_by(Game.game_date).all()
        
        for game in games:
            # Build features
            features = build_game_features(
                db, game, game.home_team_id, game.away_team_id
            )
            
            # Skip if team doesn't have enough games (features will be mostly zeros)
            if (features.get("home_win_pct_last_10", 0) == 0 and 
                features.get("away_win_pct_last_10", 0) == 0):
                # Check if teams have played enough games
                home_games_count = features.get("home_win_pct_last_10", 0) * 10
                away_games_count = features.get("away_win_pct_last_10", 0) * 10
                if home_games_count < min_games_per_team or away_games_count < min_games_per_team:
                    continue
            
            # Calculate target (1 if home team wins, 0 if away team wins)
            target = 1 if game.home_score > game.away_score else 0
            
            features["target"] = target
            all_features.append(features)
            all_targets.append(target)
    
    # Convert to DataFrame
    train_df = pd.DataFrame(all_features)
    
    # Process test season if provided
    test_df = None
    if test_season:
        test_features = []
        test_targets = []
        
        games = db.query(Game).filter(
            Game.season == test_season,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).order_by(Game.game_date).all()
        
        for game in games:
            features = build_game_features(
                db, game, game.home_team_id, game.away_team_id
            )
            
            # Skip if insufficient data
            if (features.get("home_win_pct_last_10", 0) == 0 and 
                features.get("away_win_pct_last_10", 0) == 0):
                continue
            
            target = 1 if game.home_score > game.away_score else 0
            
            features["target"] = target
            test_features.append(features)
            test_targets.append(target)
        
        test_df = pd.DataFrame(test_features)
    
    return train_df, test_df


def get_feature_columns() -> List[str]:
    """Get list of feature column names (excluding target)."""
    return [
        "home_off_rating", "home_def_rating", "home_net_rating", "home_pace",
        "home_win_pct_last_10", "home_ppg_last_10", "home_ppg_allowed_last_10",
        "away_off_rating", "away_def_rating", "away_net_rating", "away_pace",
        "away_win_pct_last_10", "away_ppg_last_10", "away_ppg_allowed_last_10",
        "home_wins_last_5", "home_losses_last_5", "home_win_streak",
        "away_wins_last_5", "away_losses_last_5", "away_win_streak",
        "h2h_home_wins", "h2h_away_wins", "h2h_avg_point_diff",
        "home_rest_days", "away_rest_days",
        "home_back_to_back", "away_back_to_back",
        "home_home_win_pct", "away_away_win_pct",
        "net_rating_diff", "win_pct_diff", "rest_days_diff"
    ]


def prepare_features_for_prediction(
    db: Session, home_team_id: int, away_team_id: int, game_date, season: str
) -> pd.DataFrame:
    """Prepare features for a single game prediction.
    
    Args:
        db: Database session
        home_team_id: Home team ID
        away_team_id: Away team ID
        game_date: Date of the game
        season: Season string
    
    Returns:
        DataFrame with single row of features
    """
    # Create a dummy game object for feature building
    class DummyGame:
        def __init__(self, game_date, season, home_team_id, away_team_id):
            self.game_date = game_date
            self.season = season
            self.home_team_id = home_team_id
            self.away_team_id = away_team_id
    
    dummy_game = DummyGame(game_date, season, home_team_id, away_team_id)
    
    features = build_game_features(db, dummy_game, home_team_id, away_team_id)
    
    # Convert to DataFrame
    df = pd.DataFrame([features])
    
    # Ensure all feature columns are present (fill missing with 0)
    feature_cols = get_feature_columns()
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
    
    # Reorder columns to match training data
    df = df[feature_cols]
    
    return df



