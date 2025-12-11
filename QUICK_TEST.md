# Quick Testing Guide

## 🚀 Quick Tests (30 seconds - 2 minutes)

### Test 1: Verify Games Parsing Works
```bash
python -c "
from app.ingestion.nba_api_client import NBAAPIClient
client = NBAAPIClient()
teams = client.get_teams()
games = client.get_games('2023-24', '2024-01-15')
print(f'✅ Got {len(games)} games for 2024-01-15')
for g in games[:3]:
    print(f'   {g[\"awayTeam\"]} @ {g[\"homeTeam\"]}: {g[\"awayScore\"]}-{g[\"homeScore\"]}')
"
```

### Test 2: Verify Box Scores Work
```bash
python -c "
from app.ingestion.nba_api_client import NBAAPIClient
client = NBAAPIClient()
# Use a real game ID from test above
box_scores = client.get_box_score('0022300555')
print(f'✅ Got {len(box_scores)} box score entries')
if box_scores:
    bs = box_scores[0]
    print(f'   Sample: {bs[\"playerName\"]} - {bs[\"points\"]} pts, {bs[\"rebounds\"]} reb')
"
```

### Test 3: Test Small Ingestion (5-10 minutes)
```bash
# This will ingest a few days of games
python test_games_boxscores.py
```

## 🏀 Full Season Test (25-30 minutes)

### Option 1: Using Test Script
```bash
python test_games_boxscores.py full
```

### Option 2: Using Main Script
```bash
python ingest_nba_data.py 2023-24
```

**What happens:**
1. Fetches all 30 teams (~30 seconds)
2. Fetches all players (~1 minute)
3. Fetches all games for season (~12-15 minutes)
   - Iterates through dates from Oct 2023 to Jun 2024
   - Shows progress every 30 days
4. Fetches box scores for all games (~12-15 minutes)
   - Shows progress every 10 games

**Expected results:**
- ~1,230 games
- ~15,000-20,000 box score entries

## ✅ Verify Results

### Check Database
```bash
python check_db.py
```

### Check via API
```bash
# Count games
curl -s http://localhost:8000/games/ | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Games in API: {len(data)}')"

# Sample game
curl -s http://localhost:8000/games/1 | python3 -m json.tool
```

### Check in Browser
1. Open http://localhost:8000/docs
2. Try `GET /games/` endpoint
3. Try `GET /games/{id}` for a specific game

## 📊 What to Expect

### Before Full Season:
- Teams: 30
- Players: ~500-600
- Games: 1 (sample)
- Box Scores: 2 (sample)

### After Full Season:
- Teams: 30 (no change)
- Players: ~500-600 (no change)
- Games: ~1,230 (+1,229)
- Box Scores: ~15,000-20,000 (+~15,000)

## ⚡ Quick Verification Commands

```bash
# Quick status check
echo "Database status:" && python check_db.py | grep -E "(teams|players|games|box_scores):"

# Test API
curl -s http://localhost:8000/health && echo " - API is running"

# Count games via API
curl -s "http://localhost:8000/games/" 2>/dev/null | python3 -c "import sys, json; print(f'Games: {len(json.load(sys.stdin))}')" || echo "No games endpoint or server not running"
```

