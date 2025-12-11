# Performance Optimization - Box Scores Ingestion

## Problem
Box score ingestion was getting extremely slow after ~350 games because:
1. **Individual commits** - Each box score committed separately (very slow)
2. **Individual duplicate checks** - One query per box score to check duplicates
3. **No batching** - Processing one at a time instead of in batches

## Solution ✅

### 1. Batch Commits
- **Before**: Commit after each box score (~1,000+ commits)
- **After**: Commit every 50 box scores (~20-30 commits total)
- **Speedup**: ~50x faster for database operations

### 2. Batch Duplicate Checking
- **Before**: One query per box score to check if it exists
- **After**: One query per batch (50 box scores) to check all at once
- **Speedup**: ~50x fewer queries

### 3. Bulk Insert
- **Before**: `db.add()` and `db.commit()` for each box score
- **After**: `db.bulk_save_objects()` for entire batch
- **Speedup**: SQLAlchemy optimizes bulk operations

## Expected Performance

### Before Optimization:
- ~350 games: 5-10 minutes
- Full season (1,383 games): **Would take 2-3 hours** ⏰

### After Optimization:
- ~350 games: 1-2 minutes
- Full season (1,383 games): **~15-20 minutes** ⚡

## How It Works Now

1. **Collect box scores** in batches of 50
2. **Check duplicates** for entire batch in one query
3. **Bulk insert** all new box scores at once
4. **Commit** once per batch

## Code Changes

- Added `_create_box_score_object()` - Creates objects without committing
- Added `_batch_insert_box_scores()` - Batch processing with duplicate checking
- Modified `ingest_from_nba_api()` - Uses batch processing instead of individual commits

## Testing

Run the test again - it should be much faster:

```bash
python test_games_boxscores.py
```

You should see:
- Progress updates every 10 games
- Box score count updates
- Much faster processing (especially after 350 games)

