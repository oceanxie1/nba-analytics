# Testing Guide

## Quick Start

### 1. Make sure the server is running:
```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Choose a testing method:

## Method 1: Interactive Swagger UI (Easiest) ⭐

1. Open your browser: http://localhost:8000/docs
2. Or use ReDoc: http://localhost:8000/redoc
3. Click on any endpoint to expand it
4. Click "Try it out"
5. Fill in parameters (if needed)
6. Click "Execute"
7. See the response below

**Best for**: Quick testing, exploring the API, seeing request/response schemas

## Method 2: Python Test Script

```bash
# Install requests if needed
pip install requests

# Run the test script
python test_api.py
```

**Best for**: Automated testing, testing multiple endpoints at once

## Method 3: curl Commands

```bash
# Health check
curl http://localhost:8000/health

# List all teams
curl http://localhost:8000/teams/

# Get specific team
curl http://localhost:8000/teams/1

# List all players
curl http://localhost:8000/players/

# Get specific player
curl http://localhost:8000/players/1

# Get player season stats
curl http://localhost:8000/players/1/stats/2023-24

# Create a new team (POST)
curl -X POST http://localhost:8000/teams/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Miami Heat",
    "abbreviation": "MIA",
    "city": "Miami",
    "conference": "East",
    "division": "Southeast"
  }'

# Filter players by team
curl "http://localhost:8000/players/?team_id=1"
```

**Best for**: Quick command-line testing, CI/CD pipelines

## Method 4: Python REPL

```python
import requests

# List teams
response = requests.get("http://localhost:8000/teams/")
print(response.json())

# Get player stats
response = requests.get("http://localhost:8000/players/1/stats/2023-24")
print(response.json())
```

## Common Test Scenarios

### ✅ Test GET endpoints (read data)
- `/teams/` - List all teams
- `/teams/{id}` - Get specific team
- `/players/` - List all players
- `/players/{id}` - Get specific player
- `/players/{id}/stats/{season}` - Get player season stats
- `/games/{id}` - Get specific game

### ✅ Test POST endpoints (create data)
- `POST /teams/` - Create a new team
- `POST /players/` - Create a new player
- `POST /games/` - Create a new game
- `POST /games/box-scores` - Create a box score

### ✅ Test filtering
- `/players/?team_id=1` - Filter players by team
- `/players/?skip=0&limit=10` - Pagination

### ✅ Test error cases
- `/teams/999` - Non-existent team (should return 404)
- `/players/999/stats/2023-24` - Non-existent player stats (should return 404)

## Expected Results

With the sample data loaded, you should see:
- **3 teams**: Lakers, Warriors, Celtics
- **3 players**: LeBron James, Stephen Curry, Jayson Tatum
- **1 game**: Lakers vs Warriors
- **2 box scores**: LeBron and Curry's stats

## Troubleshooting

**Server not running?**
```bash
uvicorn app.main:app --reload
```

**No data?**
```bash
python add_sample_data.py
```

**Connection refused?**
- Make sure server is running on port 8000
- Check if another process is using port 8000

