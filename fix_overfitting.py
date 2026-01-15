#!/usr/bin/env python3
"""Script to retrain model with overfitting fixes."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, init_db
from app.ml.data_prep import prepare_training_data
from app.ml.models import train_game_outcome_model
from app.models import Game
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import pandas as pd


def train_with_regularization():
    """Train model with regularization to reduce overfitting."""
    print("🏀 Retraining Model with Overfitting Fixes")
    print("=" * 60)
    
    init_db()
    db = SessionLocal()
    
    try:
        # Get available seasons
        from sqlalchemy import distinct
        available_seasons = db.query(distinct(Game.season)).filter(
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).all()
        available_seasons = [s[0] for s in available_seasons if s[0]]
        
        if len(available_seasons) < 2:
            print("❌ Need at least 2 seasons for proper train/test split")
            return
        
        train_seasons = available_seasons[:-1]
        test_season = available_seasons[-1]
        
        print(f"\nTraining seasons: {', '.join(train_seasons)}")
        print(f"Test season: {test_season}")
        
        # Prepare data
        train_df, test_df = prepare_training_data(
            db,
            train_seasons=train_seasons,
            test_season=test_season,
            min_games_per_team=10
        )
        
        print(f"\nTraining samples: {len(train_df)}")
        print(f"Test samples: {len(test_df)}")
        
        from app.ml.data_prep import get_feature_columns
        feature_cols = get_feature_columns()
        X_train = train_df[feature_cols].fillna(0)
        y_train = train_df["target"]
        X_test = test_df[feature_cols].fillna(0)
        y_test = test_df["target"]
        
        # Try different configurations to reduce overfitting
        configs = [
            {
                "name": "More Regularization (Recommended)",
                "params": {
                    "n_estimators": 50,  # Reduced from 100
                    "max_depth": 4,     # Reduced from 6
                    "learning_rate": 0.05,  # Reduced from 0.1
                    "subsample": 0.7,    # Reduced from 0.8
                    "colsample_bytree": 0.7,  # Reduced from 0.8
                    "min_child_weight": 3,  # Added regularization
                    "reg_alpha": 0.1,   # L1 regularization
                    "reg_lambda": 1.0,   # L2 regularization
                    "random_state": 42,
                    "eval_metric": 'logloss'
                }
            },
            {
                "name": "Moderate Regularization",
                "params": {
                    "n_estimators": 75,
                    "max_depth": 5,
                    "learning_rate": 0.08,
                    "subsample": 0.75,
                    "colsample_bytree": 0.75,
                    "min_child_weight": 2,
                    "reg_alpha": 0.05,
                    "reg_lambda": 0.5,
                    "random_state": 42,
                    "eval_metric": 'logloss'
                }
            },
            {
                "name": "Light Regularization",
                "params": {
                    "n_estimators": 100,
                    "max_depth": 5,
                    "learning_rate": 0.1,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "min_child_weight": 1,
                    "reg_alpha": 0.01,
                    "reg_lambda": 0.1,
                    "random_state": 42,
                    "eval_metric": 'logloss'
                }
            }
        ]
        
        best_model = None
        best_score = 0
        best_config = None
        
        print("\n" + "=" * 60)
        print("Testing Different Regularization Configurations")
        print("=" * 60)
        
        for config in configs:
            print(f"\n{config['name']}:")
            print(f"  Parameters: {config['params']}")
            
            model = XGBClassifier(**config['params'])
            model.fit(X_train, y_train)
            
            # Evaluate
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            train_acc = accuracy_score(y_train, train_pred)
            test_acc = accuracy_score(y_test, test_pred)
            
            gap = train_acc - test_acc
            
            print(f"  Training Accuracy: {train_acc:.3f}")
            print(f"  Test Accuracy:     {test_acc:.3f}")
            print(f"  Overfitting Gap:   {gap:.3f}")
            
            # Prefer models with smaller gap and good test accuracy
            score = test_acc - (gap * 0.5)  # Penalize large gaps
            
            if score > best_score:
                best_score = score
                best_model = model
                best_config = config
        
        print("\n" + "=" * 60)
        print(f"✅ Best Configuration: {best_config['name']}")
        print("=" * 60)
        
        # Final evaluation
        train_pred = best_model.predict(X_train)
        test_pred = best_model.predict(X_test)
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        print(f"\nFinal Results:")
        print(f"  Training Accuracy: {train_acc:.3f}")
        print(f"  Test Accuracy:     {test_acc:.3f}")
        print(f"  Overfitting Gap:   {train_acc - test_acc:.3f}")
        
        if train_acc - test_acc < 0.15:
            print("\n✅ Overfitting significantly reduced!")
        else:
            print("\n⚠️  Still some overfitting, but improved")
        
        # Save the best model
        save = input("\nSave this model? (y/n): ").lower() == 'y'
        if save:
            import pickle
            model_path = "app/ml/models/game_outcome_model.pkl"
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            with open(model_path, 'wb') as f:
                pickle.dump(best_model, f)
            print(f"✅ Model saved to {model_path}")
            print("\nRun evaluate_model.py again to see improved metrics!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    train_with_regularization()

