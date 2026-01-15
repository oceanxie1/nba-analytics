# Model Evaluation Guide

## Quick Start

Run the evaluation script:
```bash
python3 evaluate_model.py
```

This will:
1. Load your trained model
2. Evaluate on test data
3. Perform cross-validation (if multiple seasons available)
4. Analyze feature importance
5. Compare to baseline performance

---

## Understanding the Metrics

### 1. **Accuracy**
- **What it is**: Percentage of correct predictions
- **Good range**: 62-68% for NBA game predictions
- **Baseline**: ~58-60% (always predicting home team wins)

### 2. **Precision**
- **What it is**: Of all games predicted as "home win", how many actually were?
- **Formula**: True Positives / (True Positives + False Positives)
- **Interpretation**: High precision = fewer false alarms

### 3. **Recall**
- **What it is**: Of all actual "home wins", how many did we predict correctly?
- **Formula**: True Positives / (True Positives + False Negatives)
- **Interpretation**: High recall = we catch most home wins

### 4. **F1 Score**
- **What it is**: Harmonic mean of precision and recall
- **Formula**: 2 × (Precision × Recall) / (Precision + Recall)
- **Interpretation**: Balanced measure of precision and recall

### 5. **ROC AUC**
- **What it is**: Area Under the ROC Curve
- **Range**: 0.5 (random) to 1.0 (perfect)
- **Interpretation**: 
  - 0.5 = No better than random
  - 0.7+ = Good model
  - 0.8+ = Excellent model

### 6. **Confusion Matrix**
Shows where your model makes mistakes:
```
                Predicted
              Away Win  Home Win
Actual Away      TN       FP
       Home      FN       TP
```

- **TN (True Negative)**: Correctly predicted away win
- **FP (False Positive)**: Predicted home win, but away won
- **FN (False Negative)**: Predicted away win, but home won
- **TP (True Positive)**: Correctly predicted home win

---

## Cross-Validation

**What it does**: Splits your data into 5 folds, trains on 4, tests on 1, repeats 5 times.

**Why it matters**: 
- More reliable than single train/test split
- Shows how consistent your model is
- Lower standard deviation = more stable model

**Good results**:
- Mean accuracy close to test accuracy
- Low standard deviation (< 0.02)

---

## Feature Importance

Shows which features matter most for predictions.

**Top features to look for**:
- Net rating differences
- Recent win percentages
- Home/away records
- Rest days

**What to do**:
- Focus on improving top features
- Consider removing low-importance features
- Engineer new features based on important ones

---

## Baseline Comparison

Compares your model to the simplest baseline: **always predict home team wins**.

**Why it matters**: 
- Home teams win ~58-60% of NBA games
- Your model should beat this baseline
- Improvement shows your model adds value

**Good improvement**: +3-8% over baseline

---

## Interpreting Results

### ✅ Good Model Performance
- Accuracy: 65-70%
- ROC AUC: 0.70+
- F1 Score: 0.65+
- Beats baseline by 5%+

### ⚠️ Needs Improvement
- Accuracy: 60-65%
- ROC AUC: 0.60-0.70
- F1 Score: 0.60-0.65
- Beats baseline by 2-5%

### ❌ Poor Performance
- Accuracy: < 60%
- ROC AUC: < 0.60
- F1 Score: < 0.60
- Doesn't beat baseline

---

## Improving Your Model

### 1. **More Data**
- Ingest more seasons
- More games = better model

### 2. **Feature Engineering**
- Add player-level features
- Add matchup-specific features
- Add injury/rest information

### 3. **Hyperparameter Tuning**
- Try different learning rates
- Adjust max_depth
- Experiment with n_estimators

### 4. **Model Selection**
- Try different algorithms (Random Forest, Neural Networks)
- Ensemble multiple models
- Use stacking/blending

### 5. **Regular Evaluation**
- Re-evaluate as new data comes in
- Track performance over time
- Retrain periodically

---

## Example Output

```
🏀 Model Evaluation
============================================================

1. Initializing database...
2. Loading trained model...
   ✓ Model loaded successfully

3. Training Metrics (from training):
   ────────────────────────────────────────
   Training Accuracy: 0.723
   Test Accuracy:    0.658
   Test Precision:   0.671
   Test Recall:      0.712
   Test F1 Score:    0.691

📊 Evaluating on Test Set
============================================================
   Test Season: 2024-25
   Total Games: 1230
   Processing games...
   ✅ Evaluation Complete (1156 games)

   Metrics:
   ────────────────────────────────────────
   Accuracy:  0.658 (65.8%)
   Precision: 0.671
   Recall:    0.712
   F1 Score:  0.691
   ROC AUC:   0.703

   Confusion Matrix:
   ────────────────────────────────────────
   True Negatives:  342
   False Positives: 152
   False Negatives: 250
   True Positives:  412

📈 Baseline Comparison
============================================================
   Baseline Accuracy (Always Predict Home): 0.587 (58.7%)
   vs Baseline: +0.071 (7.1% improvement)
```

---

## Next Steps

1. **Run evaluation**: `python3 evaluate_model.py`
2. **Review metrics**: Check if model beats baseline
3. **Analyze features**: See which features matter most
4. **Improve**: Add more data, tune hyperparameters, engineer features
5. **Re-evaluate**: Run again after improvements

---

## Tips

- **Evaluate regularly**: After retraining, after adding data
- **Track over time**: Keep a log of performance metrics
- **Compare models**: If you try different approaches, compare results
- **Focus on what matters**: For betting, accuracy matters. For insights, feature importance matters.

