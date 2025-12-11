# Testing Guide - Games & Box Scores

## Quick Tests

### 1. Test Single Date (Fast - ~30 seconds)
```bash
python -c "
from app.ingestion.nba_api_client import NBAAPIClient
client = NBAAPIClient()
teams = client.get_teams()  # Build mapping
games = client.get_games('2023-24', '2024-01-15')
print(f'Got {len(games)} games')
for g in games[:3]:
    print(f'{g[\"awayTeam\"]} @ {g[\"homeTeam\"]}: {g[\"awayScore\"]}-{g[\"homeScore\"]}')
"
```

### 2. Test Box Score for a Game
```bash
python -c "
from app.ingestion.nba_api_client import NBAAPIClient
client = NBAAPIClient()
box_scores = client.get_box_score('0022300555')  # Use a real game ID
print(f'Got {len(box_scores)} box score entries')
if box_scores:
    print(f'Sample: {box_scores[0][\"playerName\"]} - {box_scores[0][\"points\"]} pts')
"
```

### 3. Test Full Ingestion (Recommended)
```bash
# This will ingest teams, players, games, and box scores
python test_games_boxscores.py
```

### 4. Test Full Season (Takes ~25-30 minutes)
```bash
# WARNING: This takes a long time!
python test_games_boxscores.py full
# OR
python ingest_nba_data.py 2023-24
```

## Verify Results

### Check Database
```bash
python check_db.py
```

### Check via API
```bash
# List games
curl http://localhost:8000/games/ | python3 -m json.tool

# List box scores
curl http://localhost:8000/games/box-scores/ | python3 -m json.tool

# Get specific game
curl http://localhost:8000/games/1 | python3 -m json.tool

# Get player stats
curl http://localhost:8000/players/1/stats/2023-24 | python3 -m json.tool
```

### Check in Swagger UI
1. Open http://localhost:8000/docs
2. Try the endpoints:
   - `GET /games/` - List all games
   - `GET /games/{game_id}` - Get specific game
   - `GET /games/box-scores/{box_score_id}` - Get box score

## What to Look For

### ✅ Success Indicators:
- Games count increases (should be ~1,230 for full season)
- Box scores count increases (should be ~10-15 per game)
- Games have correct dates, teams, scores
- Box scores have player names and stats
- No errors in console output

### ⚠️ Common Issues:
- **No games found**: Season might not have started yet, or date range is wrong
- **No box scores**: Games might not have been played yet, or box score data not available
- **Timeout errors**: Network issues or rate limiting (normal, will retry)
- **Team mapping errors**: Teams not in database (should be auto-fixed)

## Performance Testing

### Test Date Range (Faster)
To test with a smaller date range, modify `nba_api_client.py`:

```python
# In get_games_for_season(), change:
end_date = date(year_end, 6, 30)
# To:
end_date = date(year_start, 10, 7)  # Just first week
```

### Monitor Progress
The ingestion script shows:
- Progress updates every 30 days
- Game count as it processes
- Box score progress every 10 games

## Expected Results

### Full Season (2023-24):
- **Teams**: 30 (all NBA teams)
- **Players**: ~500-600 (active players)
- **Games**: ~1,230 (82 games × 30 teams / 2)
- **Box Scores**: ~15,000-20,000 (10-15 players × 1,230 games)

### Test Run (7 days):
- **Games**: ~50-70 games
- **Box Scores**: ~500-1,000 entries

## Troubleshooting

### If ingestion stops:
1. Check console for errors
2. Verify network connection
3. Check if NBA API is accessible
4. Try smaller date range

### If no box scores:
1. Verify games were ingested first
2. Check if games have been played (not scheduled)
3. Some games might not have box score data available

### If teams missing:
1. Teams should be auto-ingested first
2. Check team mapping is built correctly
3. Verify team abbreviations match

