"""Machine learning models for game outcome prediction."""
import os
import pickle
from typing import Optional, Dict, Tuple
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import logging

logger = logging.getLogger(__name__)

# Model storage path
MODEL_DIR = "app/ml/models"
MODEL_PATH = os.path.join(MODEL_DIR, "game_outcome_model.pkl")


def train_game_outcome_model(
    train_df: pd.DataFrame,
    test_df: Optional[pd.DataFrame] = None,
    save_model: bool = True
) -> Tuple[XGBClassifier, Dict]:
    """Train XGBoost model for game outcome prediction.
    
    Args:
        train_df: Training DataFrame with features and 'target' column
        test_df: Optional test DataFrame for evaluation
        save_model: Whether to save the trained model
    
    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    from app.ml.data_prep import get_feature_columns
    
    # Prepare features and target
    feature_cols = get_feature_columns()
    X_train = train_df[feature_cols].fillna(0)
    y_train = train_df["target"]
    
    # Initialize model
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    # Train model
    logger.info(f"Training model on {len(X_train)} samples...")
    model.fit(X_train, y_train)
    
    # Evaluate on training set
    train_pred = model.predict(X_train)
    train_acc = accuracy_score(y_train, train_pred)
    
    metrics = {
        "train_accuracy": train_acc,
        "train_samples": len(X_train)
    }
    
    # Evaluate on test set if provided
    if test_df is not None:
        X_test = test_df[feature_cols].fillna(0)
        y_test = test_df["target"]
        
        test_pred = model.predict(X_test)
        test_proba = model.predict_proba(X_test)[:, 1]
        
        metrics.update({
            "test_accuracy": accuracy_score(y_test, test_pred),
            "test_precision": precision_score(y_test, test_pred, zero_division=0),
            "test_recall": recall_score(y_test, test_pred, zero_division=0),
            "test_f1": f1_score(y_test, test_pred, zero_division=0),
            "test_samples": len(X_test)
        })
        
        # Confusion matrix
        cm = confusion_matrix(y_test, test_pred)
        metrics["confusion_matrix"] = {
            "true_negative": int(cm[0, 0]),
            "false_positive": int(cm[0, 1]),
            "false_negative": int(cm[1, 0]),
            "true_positive": int(cm[1, 1])
        }
        
        logger.info(f"Test accuracy: {metrics['test_accuracy']:.3f}")
    
    # Feature importance
    feature_importance = dict(zip(feature_cols, model.feature_importances_))
    metrics["feature_importance"] = dict(
        sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    )
    
    # Save model if requested
    if save_model:
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {MODEL_PATH}")
    
    return model, metrics


def load_game_outcome_model() -> Optional[XGBClassifier]:
    """Load trained game outcome prediction model.
    
    Returns:
        Loaded XGBoost model or None if not found
    """
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"Model not found at {MODEL_PATH}")
        return None
    
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Model loaded from {MODEL_PATH}")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None


def predict_game_outcome(
    model: XGBClassifier,
    features_df: pd.DataFrame
) -> Dict:
    """Predict game outcome using trained model.
    
    Args:
        model: Trained XGBoost model
        features_df: DataFrame with feature columns
    
    Returns:
        Dictionary with:
        - prediction: 1 (home wins) or 0 (away wins)
        - probability: Confidence score (0-1)
        - home_win_prob: Probability home team wins
        - away_win_prob: Probability away team wins
    """
    from app.ml.data_prep import get_feature_columns
    
    feature_cols = get_feature_columns()
    X = features_df[feature_cols].fillna(0)
    
    # Predict
    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    
    home_win_prob = probabilities[1]  # Class 1 = home wins
    away_win_prob = probabilities[0]  # Class 0 = away wins
    
    return {
        "prediction": int(prediction),
        "probability": float(max(home_win_prob, away_win_prob)),
        "home_win_prob": float(home_win_prob),
        "away_win_prob": float(away_win_prob),
        "predicted_winner": "home" if prediction == 1 else "away"
    }



