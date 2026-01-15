# Model Training Explained

## Overview

This document explains how to train the game outcome prediction model.

## Quick Start

```bash
# 1. Make sure you have data in your database
python ingest_nba_data.py

# 2. Train the model
python train_model.py
```

## What Happens During Training

### Step 1: Database Initialization
- Connects to your SQLite database
- Checks for available seasons with completed games

### Step 2: Data Preparation
- **If multiple seasons**: Uses older seasons for training, newest for testing
- **If single season**: Splits by date (80% train, 20% test)

### Step 3: Feature Engineering
For each game, calculates:
- Team rolling stats (last 10 games): Offensive/Defensive/Net Rating, Pace, Win %
- Recent form (last 5 games): Wins, Losses, Win Streak
- Head-to-head record: Wins, Point differential
- Rest days: Days since last game
- Home/Away records: Win percentages

### Step 4: Model Training
- Trains XGBoost classifier
- Evaluates on test set
- Calculates metrics (accuracy, precision, recall, F1)

### Step 5: Model Persistence
- Saves model to `app/ml/models/game_outcome_model.pkl`
- Saves metrics to `app/ml/models/training_metrics.json`

## Training Output

After training, you'll see:

```
🏀 Training Game Outcome Prediction Model
==================================================

1. Initializing database...

2. Found seasons in database: 2023-24, 2024-25
   Using multiple seasons for training/test split
   Training seasons: 2023-24
   Test season: 2024-25
   ✓ Training samples: 1279
   ✓ Test samples: 1266

3. Training XGBoost model...

4. Training Results:
==================================================
Training Accuracy: 0.997 (1279 samples)

Test Set Performance:
  Accuracy:  0.657
  Precision: 0.675
  Recall:    0.722
  F1 Score:  0.698
  Samples:   1266

Confusion Matrix:
  True Negatives:  331
  False Positives: 241
  False Negatives: 193
  True Positives:  501

5. Top 10 Most Important Features:
==================================================
   1. home_home_win_pct         0.0905
   2. away_away_win_pct         0.0629
   3. away_back_to_back         0.0451
   ...
```

## Understanding the Metrics

### Accuracy
- Overall percentage of correct predictions
- **65.7%** is good for NBA predictions (baseline is ~58-60%)

### Precision
- Of games predicted as "home wins", how many actually did?
- **67.5%** means when we predict home wins, we're right 67.5% of the time

### Recall
- Of all games where home actually won, how many did we predict correctly?
- **72.2%** means we catch 72.2% of all home wins

### F1 Score
- Harmonic mean of precision and recall
- **69.8%** balances precision and recall

### Confusion Matrix
- **True Negatives (331)**: Correctly predicted away wins
- **False Positives (241)**: Predicted home wins, but away actually won
- **False Negatives (193)**: Predicted away wins, but home actually won
- **True Positives (501)**: Correctly predicted home wins

## Feature Importance

The model shows which features matter most:

1. **home_home_win_pct** (9.0%): Home team's home record - most important!
2. **away_away_win_pct** (6.3%): Away team's away record
3. **away_back_to_back** (4.5%): Whether away team is on back-to-back

This tells us:
- Home court advantage is real and important
- Team records matter
- Rest days matter (back-to-back games hurt performance)

## Using the Trained Model

### Via API

```bash
# Start the server
uvicorn app.main:app --reload

# Make a prediction
curl -X POST "http://localhost:8000/games/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "home_team_id": 14,
    "away_team_id": 6,
    "game_date": "2025-01-15",
    "season": "2024-25"
  }'
```

### Via Script

```bash
python test_predictions.py
```

## Troubleshooting

### "No completed games found"
- You need to ingest game data first
- Run: `python ingest_nba_data.py`

### "Less than 100 training samples"
- Model may not perform well with so little data
- Ingest more seasons: `python ingest_multiple_seasons.py --start-year 2020 --end-year 2024`

### "Model not found"
- Train the model first: `python train_model.py`
- Check that `app/ml/models/game_outcome_model.pkl` exists

### Low Accuracy
- NBA games are inherently unpredictable
- 60-70% accuracy is actually good!
- Try ingesting more historical data
- Consider hyperparameter tuning

## Next Steps

1. **Improve the model:**
   - Hyperparameter tuning
   - Cross-validation
   - Feature engineering enhancements

2. **Add more features:**
   - Injury reports
   - Schedule strength
   - Travel distance
   - Referee tendencies

3. **Build other models:**
   - Player performance prediction
   - Point spread prediction
   - Over/under prediction



