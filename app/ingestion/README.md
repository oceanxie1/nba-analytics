# Data Ingestion Module

This module handles ingesting NBA data from various sources into the database.

## Structure

- `nba_client.py` - NBA API client for fetching data from stats.nba.com
- `ingest.py` - Core ingestion functions (teams, players, games, box scores)
- `csv_ingest.py` - CSV-based ingestion as an alternative

## Usage

### Option 1: NBA API (Primary)

```bash
# Ingest current season
python ingest_nba_data.py

# Ingest specific season
python ingest_nba_data.py 2023-24
```

**Note**: The NBA API (stats.nba.com) may require:
- Proper headers (already configured)
- Rate limiting (handled automatically)
- API endpoint adjustments based on actual response format

### Option 2: CSV Import

If the API doesn't work, you can use CSV files:

```python
from app.ingestion.csv_ingest import *
from app.db import SessionLocal

db = SessionLocal()

# Ingest teams
team_map = ingest_teams_from_csv("teams.csv", db)

# Ingest players
player_map = ingest_players_from_csv("players.csv", team_map, db)

# Ingest games
game_ids = ingest_games_from_csv("games.csv", team_map, db)

# Ingest box scores
box_score_ids = ingest_box_scores_from_csv("box_scores.csv", player_map, db)
```

### Option 3: Manual Data Entry

You can also use the existing API endpoints to manually add data:
- `POST /teams/` - Add teams
- `POST /players/` - Add players
- `POST /games/` - Add games
- `POST /games/box-scores` - Add box scores

## Data Formats

### Teams CSV
```csv
name,abbreviation,city,conference,division
Los Angeles Lakers,LAL,Los Angeles,West,Pacific
```

### Players CSV
```csv
name,position,height,weight,birth_date,team_abbreviation
LeBron James,SF,6-9,250,1984-12-30,LAL
```

### Games CSV
```csv
game_date,season,home_team,away_team,home_score,away_score
2024-01-15,2023-24,LAL,GSW,120,115
```

### Box Scores CSV
```csv
game_id,player_name,minutes,points,rebounds,assists,steals,blocks,turnovers,personal_fouls,fgm,fga,fg3m,fg3a,ftm,fta,plus_minus
1,LeBron James,38.5,32,8,12,2,1,3,2,12,22,3,7,5,6,15
```

## Error Handling

- Duplicate detection: Won't create duplicate teams/players/games
- Missing data: Handles missing fields gracefully
- Rate limiting: Built into NBA API client
- Validation: Basic validation before database insertion

