#!/usr/bin/env python3
"""Comprehensive model evaluation script."""
import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, init_db
from app.ml.models import load_game_outcome_model, predict_game_outcome
from app.ml.data_prep import prepare_training_data, prepare_features_for_prediction, get_feature_columns
from app.models import Game
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
from sklearn.model_selection import cross_val_score, StratifiedKFold


def load_saved_metrics():
    """Load previously saved training metrics."""
    metrics_path = "app/ml/models/training_metrics.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return json.load(f)
    return None


def evaluate_on_test_set(db, model, test_season=None):
    """Evaluate model on a test set of games."""
    print("\n" + "=" * 60)
    print("📊 Evaluating on Test Set")
    print("=" * 60)
    
    # Get test games
    if test_season:
        games = db.query(Game).filter(
            Game.season == test_season,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).order_by(Game.game_date).all()
    else:
        # Use most recent season
        latest_season = db.query(Game.season).filter(
            Game.home_score.isnot(None)
        ).order_by(Game.game_date.desc()).first()
        if not latest_season:
            print("❌ No completed games found.")
            return None
        
        test_season = latest_season[0]
        games = db.query(Game).filter(
            Game.season == test_season,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).order_by(Game.game_date).all()
    
    print(f"   Test Season: {test_season}")
    print(f"   Total Games: {len(games)}")
    
    # Build features and get predictions
    from app.ml.features import build_game_features
    
    predictions = []
    actuals = []
    probabilities = []
    
    print("\n   Processing games...")
    for i, game in enumerate(games):
        if (i + 1) % 50 == 0:
            print(f"   Processed {i + 1}/{len(games)} games...")
        
        try:
            features = build_game_features(
                db, game, game.home_team_id, game.away_team_id
            )
            
            # Skip if insufficient data
            if (features.get("home_win_pct_last_10", 0) == 0 and 
                features.get("away_win_pct_last_10", 0) == 0):
                continue
            
            # Prepare features DataFrame
            feature_cols = get_feature_columns()
            features_df = pd.DataFrame([features])
            for col in feature_cols:
                if col not in features_df.columns:
                    features_df[col] = 0.0
            features_df = features_df[feature_cols]
            
            # Get prediction
            result = predict_game_outcome(model, features_df)
            
            predictions.append(result['prediction'])
            actuals.append(1 if game.home_score > game.away_score else 0)
            probabilities.append(result['home_win_prob'])
            
        except Exception as e:
            print(f"   Warning: Skipping game {game.id}: {e}")
            continue
    
    if len(predictions) == 0:
        print("❌ No valid predictions generated.")
        return None
    
    # Calculate metrics
    accuracy = accuracy_score(actuals, predictions)
    precision = precision_score(actuals, predictions, zero_division=0)
    recall = recall_score(actuals, predictions, zero_division=0)
    f1 = f1_score(actuals, predictions, zero_division=0)
    
    # ROC AUC
    try:
        roc_auc = roc_auc_score(actuals, probabilities)
    except:
        roc_auc = None
    
    # Confusion matrix
    cm = confusion_matrix(actuals, predictions)
    tn, fp, fn, tp = cm.ravel()
    
    print(f"\n   ✅ Evaluation Complete ({len(predictions)} games)")
    print(f"\n   Metrics:")
    print(f"   {'─' * 40}")
    print(f"   Accuracy:  {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"   Precision: {precision:.3f}")
    print(f"   Recall:    {recall:.3f}")
    print(f"   F1 Score:  {f1:.3f}")
    if roc_auc:
        print(f"   ROC AUC:   {roc_auc:.3f}")
    
    print(f"\n   Confusion Matrix:")
    print(f"   {'─' * 40}")
    print(f"   True Negatives (Away Win Correct):  {tn:4d}")
    print(f"   False Positives (Away Win Predicted, Home Won): {fp:4d}")
    print(f"   False Negatives (Home Win Predicted, Away Won): {fn:4d}")
    print(f"   True Positives (Home Win Correct):  {tp:4d}")
    
    # Classification report
    print(f"\n   Classification Report:")
    print(f"   {'─' * 40}")
    report = classification_report(actuals, predictions, 
                                   target_names=['Away Win', 'Home Win'],
                                   zero_division=0)
    print(report)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc,
        'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)},
        'samples': len(predictions)
    }


def cross_validate_model(db, train_seasons):
    """Perform cross-validation on the model."""
    print("\n" + "=" * 60)
    print("🔄 Cross-Validation")
    print("=" * 60)
    
    # Prepare training data
    train_df, _ = prepare_training_data(
        db,
        train_seasons=train_seasons,
        test_season=None,
        min_games_per_team=10
    )
    
    if len(train_df) < 100:
        print("⚠️  Not enough data for cross-validation (need at least 100 samples)")
        return None
    
    from app.ml.models import train_game_outcome_model
    from app.ml.data_prep import get_feature_columns
    
    feature_cols = get_feature_columns()
    X = train_df[feature_cols].fillna(0)
    y = train_df["target"]
    
    # Train a model for cross-validation
    model, _ = train_game_outcome_model(train_df, save_model=False)
    
    # Perform 5-fold cross-validation
    print(f"   Performing 5-fold cross-validation on {len(train_df)} samples...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    
    print(f"\n   Cross-Validation Results:")
    print(f"   {'─' * 40}")
    print(f"   Fold Scores: {[f'{s:.3f}' for s in cv_scores]}")
    print(f"   Mean Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    print(f"   Min: {cv_scores.min():.3f}")
    print(f"   Max: {cv_scores.max():.3f}")
    
    return {
        'mean_accuracy': float(cv_scores.mean()),
        'std_accuracy': float(cv_scores.std()),
        'min_accuracy': float(cv_scores.min()),
        'max_accuracy': float(cv_scores.max()),
        'fold_scores': [float(s) for s in cv_scores]
    }


def analyze_feature_importance(model):
    """Analyze and display feature importance."""
    print("\n" + "=" * 60)
    print("🎯 Feature Importance Analysis")
    print("=" * 60)
    
    feature_cols = get_feature_columns()
    importances = model.feature_importances_
    
    # Create DataFrame for easier analysis
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print(f"\n   Top 15 Most Important Features:")
    print(f"   {'─' * 50}")
    for i, row in importance_df.head(15).iterrows():
        print(f"   {row['feature']:30s} {row['importance']:.4f}")
    
    # Feature categories
    categories = {
        'Rolling Stats': [f for f in feature_cols if 'rating' in f or 'pace' in f or 'ppg' in f],
        'Recent Form': [f for f in feature_cols if 'last_5' in f or 'streak' in f or 'last_10' in f],
        'Head-to-Head': [f for f in feature_cols if 'h2h' in f],
        'Rest Days': [f for f in feature_cols if 'rest' in f or 'back_to_back' in f],
        'Home/Away Records': [f for f in feature_cols if 'home_win_pct' in f or 'away_win_pct' in f],
        'Differentials': [f for f in feature_cols if 'diff' in f]
    }
    
    print(f"\n   Importance by Category:")
    print(f"   {'─' * 50}")
    for category, features in categories.items():
        cat_importance = importance_df[importance_df['feature'].isin(features)]['importance'].sum()
        print(f"   {category:20s} {cat_importance:.4f}")
    
    return importance_df


def compare_to_baseline(db, test_season=None):
    """Compare model performance to baseline (home team always wins)."""
    print("\n" + "=" * 60)
    print("📈 Baseline Comparison")
    print("=" * 60)
    
    # Get test games
    if test_season:
        games = db.query(Game).filter(
            Game.season == test_season,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).all()
    else:
        latest_season = db.query(Game.season).filter(
            Game.home_score.isnot(None)
        ).order_by(Game.game_date.desc()).first()
        if not latest_season:
            return None
        test_season = latest_season[0]
        games = db.query(Game).filter(
            Game.season == test_season,
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).all()
    
    # Baseline: always predict home win
    baseline_predictions = [1] * len(games)
    actuals = [1 if g.home_score > g.away_score else 0 for g in games]
    
    baseline_accuracy = accuracy_score(actuals, baseline_predictions)
    home_win_rate = sum(actuals) / len(actuals) if actuals else 0
    
    print(f"\n   Test Season: {test_season}")
    print(f"   Total Games: {len(games)}")
    print(f"   Home Win Rate: {home_win_rate:.3f} ({home_win_rate*100:.1f}%)")
    print(f"   Baseline Accuracy (Always Predict Home): {baseline_accuracy:.3f} ({baseline_accuracy*100:.1f}%)")
    
    return {
        'baseline_accuracy': baseline_accuracy,
        'home_win_rate': home_win_rate,
        'total_games': len(games)
    }


def main():
    """Main evaluation function."""
    print("🏀 Model Evaluation")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    db = SessionLocal()
    
    try:
        # Load model
        print("\n2. Loading trained model...")
        model = load_game_outcome_model()
        if not model:
            print("❌ No trained model found. Please run train_model.py first.")
            return 1
        
        print("   ✓ Model loaded successfully")
        
        # Load saved metrics
        saved_metrics = load_saved_metrics()
        if saved_metrics:
            print("\n3. Training Metrics (from training):")
            print("   " + "─" * 40)
            if 'train_accuracy' in saved_metrics:
                print(f"   Training Accuracy: {saved_metrics['train_accuracy']:.3f}")
            if 'test_accuracy' in saved_metrics:
                print(f"   Test Accuracy:    {saved_metrics['test_accuracy']:.3f}")
                print(f"   Test Precision:   {saved_metrics.get('test_precision', 0):.3f}")
                print(f"   Test Recall:      {saved_metrics.get('test_recall', 0):.3f}")
                print(f"   Test F1 Score:    {saved_metrics.get('test_f1', 0):.3f}")
        
        # Get available seasons
        from sqlalchemy import distinct
        available_seasons = db.query(distinct(Game.season)).filter(
            Game.home_score.isnot(None),
            Game.away_score.isnot(None)
        ).all()
        available_seasons = [s[0] for s in available_seasons if s[0]]
        
        if len(available_seasons) == 0:
            print("❌ No completed games found in database.")
            return 1
        
        print(f"\n   Available seasons: {', '.join(available_seasons)}")
        
        # Evaluate on test set
        if len(available_seasons) > 1:
            test_season = available_seasons[-1]  # Most recent
            test_metrics = evaluate_on_test_set(db, model, test_season)
        else:
            test_metrics = evaluate_on_test_set(db, model, available_seasons[0])
        
        # Cross-validation (if enough data)
        if len(available_seasons) > 1:
            train_seasons = available_seasons[:-1]
            cv_metrics = cross_validate_model(db, train_seasons)
        else:
            print("\n⚠️  Skipping cross-validation (need multiple seasons)")
            cv_metrics = None
        
        # Feature importance
        importance_df = analyze_feature_importance(model)
        
        # Baseline comparison
        baseline_metrics = compare_to_baseline(db, test_season if len(available_seasons) > 1 else available_seasons[0])
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 Evaluation Summary")
        print("=" * 60)
        
        if test_metrics:
            print(f"\n   Test Set Performance:")
            print(f"   {'─' * 40}")
            print(f"   Accuracy:  {test_metrics['accuracy']:.3f} ({test_metrics['accuracy']*100:.1f}%)")
            if baseline_metrics:
                improvement = test_metrics['accuracy'] - baseline_metrics['baseline_accuracy']
                print(f"   vs Baseline: +{improvement:.3f} ({improvement*100:.1f}% improvement)")
            print(f"   Precision: {test_metrics['precision']:.3f}")
            print(f"   Recall:    {test_metrics['recall']:.3f}")
            print(f"   F1 Score:  {test_metrics['f1']:.3f}")
            if test_metrics.get('roc_auc'):
                print(f"   ROC AUC:   {test_metrics['roc_auc']:.3f}")
        
        if cv_metrics:
            print(f"\n   Cross-Validation:")
            print(f"   {'─' * 40}")
            print(f"   Mean Accuracy: {cv_metrics['mean_accuracy']:.3f} ± {cv_metrics['std_accuracy']:.3f}")
        
        print("\n✅ Evaluation complete!")
        print("\n💡 Tips for improving your model:")
        print("   - More training data usually improves performance")
        print("   - Try hyperparameter tuning (learning_rate, max_depth, etc.)")
        print("   - Consider feature engineering based on top important features")
        print("   - Monitor performance over time as new data comes in")
        
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    exit(main())

