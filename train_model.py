#!/usr/bin/env python3
"""Script to train the game outcome prediction model."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, init_db
from app.ml.data_prep import prepare_training_data
from app.ml.models import train_game_outcome_model
from app.ml.features import build_game_features
from app.models import Game
import pandas as pd
import json


def main():
    """Train the game outcome prediction model."""
    print("🏀 Training Game Outcome Prediction Model")
    print("=" * 50)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check what seasons are available
        from sqlalchemy import func, distinct
        available_seasons = db.query(distinct(Game.season)).filter(
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).all()
        available_seasons = [s[0] for s in available_seasons if s[0]]
        
        if not available_seasons:
            print("\n❌ Error: No completed games found in database.")
            print("   Please ingest game data first using the ingestion pipeline.")
            return 1
        
        print(f"\n2. Found seasons in database: {', '.join(available_seasons)}")
        
        # If only one season, split it into train/test
        if len(available_seasons) == 1:
            season = available_seasons[0]
            print(f"   Only one season available ({season}).")
            print("   Will split into 80% training, 20% testing based on game date.")
            
            # Get all games for this season
            all_games = db.query(Game).filter(
                Game.season == season,
                Game.home_score.isnot(None),
                Game.away_score.isnot(None)
            ).order_by(Game.game_date).all()
            
            if len(all_games) < 50:
                print(f"\n⚠️  Warning: Only {len(all_games)} games found.")
                print("   Need at least 50 games for meaningful training.")
                print("   Consider ingesting more data.")
                response = input("   Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    return 0
            
            # Split by date: 80% train, 20% test
            split_idx = int(len(all_games) * 0.8)
            train_games = all_games[:split_idx]
            test_games = all_games[split_idx:]
            
            print(f"   Training: {len(train_games)} games (first 80%)")
            print(f"   Testing: {len(test_games)} games (last 20%)")
            
            # Build features for training games
            print("\n   Building features for training games...")
            train_features = []
            for game in train_games:
                try:
                    features = build_game_features(
                        db, game, game.home_team_id, game.away_team_id
                    )
                    # Skip if insufficient data
                    if (features.get("home_win_pct_last_10", 0) == 0 and 
                        features.get("away_win_pct_last_10", 0) == 0):
                        continue
                    target = 1 if game.home_score > game.away_score else 0
                    features["target"] = target
                    train_features.append(features)
                except Exception as e:
                    print(f"   Warning: Skipping game {game.id}: {e}")
                    continue
            
            # Build features for test games
            print("   Building features for test games...")
            test_features = []
            for game in test_games:
                try:
                    features = build_game_features(
                        db, game, game.home_team_id, game.away_team_id
                    )
                    if (features.get("home_win_pct_last_10", 0) == 0 and 
                        features.get("away_win_pct_last_10", 0) == 0):
                        continue
                    target = 1 if game.home_score > game.away_score else 0
                    features["target"] = target
                    test_features.append(features)
                except Exception as e:
                    print(f"   Warning: Skipping game {game.id}: {e}")
                    continue
            
            train_df = pd.DataFrame(train_features)
            test_df = pd.DataFrame(test_features) if test_features else None
            
        else:
            # Multiple seasons available - use older for training, newest for testing
            print("   Using multiple seasons for training/test split")
            train_seasons = available_seasons[:-1]  # All but last
            test_season = available_seasons[-1]     # Most recent
            
            print(f"   Training seasons: {', '.join(train_seasons)}")
            print(f"   Test season: {test_season}")
            
            train_df, test_df = prepare_training_data(
                db,
                train_seasons=train_seasons,
                test_season=test_season,
                min_games_per_team=10
            )
        
        print(f"   ✓ Training samples: {len(train_df)}")
        if test_df is not None:
            print(f"   ✓ Test samples: {len(test_df)}")
        
        # Check if we have enough data
        if len(train_df) < 100:
            print("\n⚠️  Warning: Less than 100 training samples. Model may not perform well.")
            print("   Consider ingesting more historical data.")
            response = input("   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("   Training cancelled.")
                return
        
        # Train model
        print("\n3. Training XGBoost model...")
        model, metrics = train_game_outcome_model(
            train_df,
            test_df=test_df,
            save_model=True
        )
        
        # Print results
        print("\n4. Training Results:")
        print("=" * 50)
        print(f"Training Accuracy: {metrics['train_accuracy']:.3f} ({metrics['train_samples']} samples)")
        
        if 'test_accuracy' in metrics:
            print(f"\nTest Set Performance:")
            print(f"  Accuracy:  {metrics['test_accuracy']:.3f}")
            print(f"  Precision: {metrics['test_precision']:.3f}")
            print(f"  Recall:    {metrics['test_recall']:.3f}")
            print(f"  F1 Score:  {metrics['test_f1']:.3f}")
            print(f"  Samples:   {metrics['test_samples']}")
            
            if 'confusion_matrix' in metrics:
                cm = metrics['confusion_matrix']
                print(f"\nConfusion Matrix:")
                print(f"  True Negatives:  {cm['true_negative']}")
                print(f"  False Positives: {cm['false_positive']}")
                print(f"  False Negatives: {cm['false_negative']}")
                print(f"  True Positives:  {cm['true_positive']}")
        
        # Feature importance
        print(f"\n5. Top 10 Most Important Features:")
        print("=" * 50)
        feature_importance = metrics.get('feature_importance', {})
        for i, (feature, importance) in enumerate(list(feature_importance.items())[:10], 1):
            print(f"  {i:2d}. {feature:25s} {importance:.4f}")
        
        # Save metrics
        metrics_path = "app/ml/models/training_metrics.json"
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        with open(metrics_path, 'w') as f:
            # Convert numpy types to native Python types for JSON
            import numpy as np
            
            def convert_to_native(obj):
                """Recursively convert numpy types to native Python types."""
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_to_native(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_native(item) for item in obj]
                else:
                    return obj
            
            json_metrics = convert_to_native(metrics)
            json.dump(json_metrics, f, indent=2)
        
        print(f"\n✓ Metrics saved to {metrics_path}")
        print("\n✅ Model training complete!")
        print("\nYou can now use the prediction endpoint:")
        print("  POST /games/predict")
        
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    exit(main())



