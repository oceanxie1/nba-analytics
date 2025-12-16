# NBA Analytics Platform - System Architecture

## Table of Contents
1. [High-Level Overview](#high-level-overview)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Database Schema](#database-schema)
5. [API Architecture](#api-architecture)
6. [Data Ingestion Pipeline](#data-ingestion-pipeline)
7. [File Structure](#file-structure)
8. [Technology Stack](#technology-stack)
9. [Process Flows](#process-flows)

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    NBA Analytics Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   External    │         │   FastAPI    │                     │
│  │   NBA API     │────────▶│   Backend    │                     │
│  │ (nba_api)     │         │   (REST)     │                     │
│  └──────────────┘         └──────┬───────┘                     │
│                                   │                               │
│                                   ▼                               │
│                          ┌──────────────┐                        │
│                          │   SQLite DB  │                        │
│                          │  (SQLAlchemy)│                        │
│                          └──────────────┘                        │
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   Clients    │────────▶│   API Docs    │                     │
│  │  (Browsers,  │         │  (Swagger)   │                     │
│  │   Mobile,    │         │              │                     │
│  │   Postman)   │         └──────────────┘                     │
│  └──────────────┘                                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. **FastAPI Application** (`app/main.py`)
- **Purpose**: Main web server and API gateway
- **Responsibilities**:
  - HTTP request handling
  - Route registration
  - API documentation (Swagger)
  - Database initialization on startup
  - Health checks

### 2. **Database Layer** (`app/db.py`)
- **Purpose**: Database connection and session management
- **Technology**: SQLAlchemy ORM
- **Database**: SQLite (dev)
- **Key Functions**:
  - `get_db()`: Dependency injection for database sessions
  - `init_db()`: Creates tables and indexes
  - `SessionLocal`: Session factory

### 3. **Data Models** (`app/models.py`)
- **Purpose**: Database schema definition
- **Models**:
  - `Team`: NBA teams
  - `Player`: NBA players
  - `Game`: NBA games
  - `BoxScore`: Player performance in games

### 4. **API Routers** (`app/routers/`)
- **Purpose**: RESTful API endpoints
- **Routers**:
  - `players.py`: Player endpoints
  - `teams.py`: Team endpoints
  - `games.py`: Game and box score endpoints

### 5. **Data Ingestion** (`app/ingestion/`)
- **Purpose**: Fetch and store NBA data
- **Components**:
  - `nba_api_client.py`: NBA API client (nba_api library)
  - `nba_client.py`: Direct API client (fallback)
  - `ingest.py`: Core ingestion logic
  - `csv_ingest.py`: CSV import utilities

### 6. **Schemas** (`app/schemas.py`)
- **Purpose**: Request/response validation (Pydantic)
- **Types**: Request schemas, response schemas, aggregated stats

### 7. **Analytics** (`app/analytics/`)
- **Purpose**: Future ML/feature engineering
- **Status**: Placeholder for future development

---

## Data Flow

### Data Ingestion Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Ingestion Pipeline                       │
└─────────────────────────────────────────────────────────────────┘

1. User runs: python ingest_nba_data.py
   │
   ▼
2. ingest_from_nba_api() called
   │
   ├─▶ NBAAPIClient.get_teams()
   │   │
   │   └─▶ nba_api.stats.static.teams.get_teams()
   │       │
   │       └─▶ Returns: List[TeamDict]
   │
   ├─▶ ingest_teams() → SQLite DB
   │   │
   │   └─▶ INSERT INTO teams (...)
   │
   ├─▶ NBAAPIClient.get_players()
   │   │
   │   └─▶ nba_api.stats.endpoints.commonallplayers
   │       │
   │       └─▶ Returns: List[PlayerDict]
   │
   ├─▶ ingest_players() → SQLite DB
   │   │
   │   └─▶ INSERT INTO players (...)
   │
   ├─▶ NBAAPIClient.get_games(season="2023-24")
   │   │
   │   ├─▶ Iterate through dates (Oct 1 - Jun 30)
   │   │
   │   ├─▶ ScoreboardV2(game_date=date_str)
   │   │
   │   └─▶ Returns: List[GameDict]
   │
   ├─▶ ingest_game() → SQLite DB
   │   │
   │   └─▶ INSERT INTO games (...)
   │
   └─▶ For each game:
       │
       ├─▶ NBAAPIClient.get_box_score(game_id)
       │   │
       │   ├─▶ BoxScoreTraditionalV2(game_id=game_id)
       │   │
       │   ├─▶ Parse pandas DataFrame (itertuples)
       │   │
       │   └─▶ Returns: List[BoxScoreDict]
       │
       └─▶ _batch_insert_box_scores_optimized()
           │
           ├─▶ Check in-memory duplicates (inserted_pairs set)
           │
           ├─▶ Check DB duplicates (if batch ≤ 100)
           │
           └─▶ db.bulk_save_objects() + commit()
               │
               └─▶ INSERT INTO box_scores (...) [200 at a time]
```

### API Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      API Request Flow                            │
└─────────────────────────────────────────────────────────────────┘

Client Request
   │
   ▼
FastAPI Router (app/routers/*.py)
   │
   ├─▶ Request Validation (Pydantic schemas)
   │
   ├─▶ Dependency Injection (get_db())
   │   │
   │   └─▶ Creates database session
   │
   ├─▶ Business Logic
   │   │
   │   ├─▶ Query database (SQLAlchemy ORM)
   │   │
   │   └─▶ Transform data (Pydantic schemas)
   │
   └─▶ Response (JSON)
       │
       └─▶ Client receives data
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    Team     │         │   Player    │         │    Game     │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ id (PK)     │◄──┐     │ id (PK)     │         │ id (PK)     │
│ name        │   │     │ name        │         │ game_date   │
│ abbreviation│   │     │ position    │         │ season      │
│ city        │   │     │ height      │         │ home_team_id│──┐
│ conference  │   │     │ weight      │         │ away_team_id│──┤
│ division    │   │     │ birth_date  │         │ home_score  │  │
└─────────────┘   │     │ team_id (FK)├─────────▶│ away_score  │  │
                  │     └─────────────┘         └──────┬──────┘  │
                  │                                    │         │
                  │                                    │         │
                  └────────────────────────────────────┼─────────┘
                                                       │
                                                       ▼
                                              ┌─────────────┐
                                              │  BoxScore   │
                                              ├─────────────┤
                                              │ id (PK)     │
                                              │ game_id (FK)├──┐
                                              │ player_id   │──┤
                                              │ minutes     │  │
                                              │ points      │  │
                                              │ rebounds    │  │
                                              │ assists     │  │
                                              │ steals      │  │
                                              │ blocks      │  │
                                              │ turnovers   │  │
                                              │ personal_   │  │
                                              │   fouls     │  │
                                              │ fgm, fga    │  │
                                              │ fg3m, fg3a  │  │
                                              │ ftm, fta    │  │
                                              │ plus_minus  │  │
                                              │             │  │
                                              │ UNIQUE      │  │
                                              │ (game_id,   │  │
                                              │  player_id) │  │
                                              └─────────────┘  │
                                                               │
                                                               └──┐
                                                                  │
                                                          ┌───────┴───────┐
                                                          │ Relationships │
                                                          ├───────────────┤
                                                          │ Team 1──N Player│
                                                          │ Team 1──N Game │
                                                          │ Player 1──N BoxScore│
                                                          │ Game 1──N BoxScore│
                                                          └───────────────┘
```

### Table Details

#### `teams`
- **Primary Key**: `id`
- **Unique Constraints**: `name`, `abbreviation`
- **Indexes**: `id`, `name`, `abbreviation`
- **Relationships**: 
  - One-to-Many with `players`
  - One-to-Many with `games` (home/away)

#### `players`
- **Primary Key**: `id`
- **Foreign Key**: `team_id` → `teams.id`
- **Indexes**: `id`, `name`
- **Relationships**:
  - Many-to-One with `team`
  - One-to-Many with `box_scores`

#### `games`
- **Primary Key**: `id`
- **Foreign Keys**: `home_team_id`, `away_team_id` → `teams.id`
- **Indexes**: `id`, `game_date`, `season`
- **Relationships**:
  - Many-to-One with `home_team`, `away_team`
  - One-to-Many with `box_scores`

#### `box_scores`
- **Primary Key**: `id`
- **Foreign Keys**: `game_id` → `games.id`, `player_id` → `players.id`
- **Unique Constraint**: `(game_id, player_id)` - ensures one box score per player per game
- **Composite Index**: `(game_id, player_id)` for fast duplicate checks
- **Indexes**: `id`, `game_id`, `player_id`
- **Relationships**:
  - Many-to-One with `game`
  - Many-to-One with `player`

---

## API Architecture

### API Endpoints

#### Base URL
```
http://localhost:8000
```

#### Root Endpoints
```
GET  /              → API info
GET  /health        → Health check
GET  /docs          → Swagger UI
```

#### Teams Endpoints (`/teams`)
```
GET  /teams                    → List all teams
GET  /teams/{team_id}          → Get team by ID
POST /teams                    → Create new team
```

#### Players Endpoints (`/players`)
```
GET  /players                  → List all players
     ?skip=0&limit=100&team_id=1
GET  /players/{player_id}      → Get player by ID
GET  /players/{player_id}/stats?season=2023-24
                              → Get player season stats
POST /players                 → Create new player
```

#### Games Endpoints (`/games`)
```
GET  /games                    → List all games
     ?skip=0&limit=100&season=2023-24
GET  /games/{game_id}          → Get game by ID
GET  /games/{game_id}/box-scores
                              → Get box scores for game
POST /games                    → Create new game
POST /games/{game_id}/box-scores
                              → Create box score
```

### Request/Response Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ HTTP Request
     │ GET /players/123/stats?season=2023-24
     ▼
┌─────────────────────────────────────┐
│  FastAPI Router                     │
│  app/routers/players.py             │
│                                      │
│  @router.get("/{player_id}/stats")  │
└────┬────────────────────────────────┘
     │
     ├─▶ Pydantic Schema Validation
     │   (app/schemas.py)
     │
     ├─▶ Dependency Injection
     │   get_db() → SessionLocal()
     │
     ├─▶ Business Logic
     │   │
     │   ├─▶ Query Player
     │   │   db.query(Player).filter(id=123)
     │   │
     │   ├─▶ Query BoxScores
     │   │   db.query(BoxScore)
     │   │     .join(Game)
     │   │     .filter(player_id=123, season="2023-24")
     │   │
     │   └─▶ Aggregate Stats
     │       SUM(points), AVG(rebounds), etc.
     │
     └─▶ Response Schema
         (Pydantic) → JSON
         │
         ▼
┌──────────┐
│  Client  │
│  Receives│
│  JSON    │
└──────────┘
```

---

## Data Ingestion Pipeline

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Data Ingestion Components                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ ingest_nba_data.py│  (Entry point)
│                  │
│ - CLI script     │
│ - Calls ingest_  │
│   from_nba_api() │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ app/ingestion/ingest.py                                     │
│                                                              │
│ ingest_from_nba_api()                                       │
│   ├─▶ ingest_teams()                                        │
│   ├─▶ ingest_players()                                      │
│   ├─▶ ingest_game()                                         │
│   └─▶ _batch_insert_box_scores_optimized()                  │
│       ├─▶ In-memory duplicate tracking                      │
│       ├─▶ Database duplicate checking                      │
│       └─▶ Bulk insert (200 at a time)                      │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ app/ingestion/nba_api_client.py                            │
│                                                              │
│ NBAAPIClient (PRIMARY - uses nba_api library)              │
│   ├─▶ get_teams()                                           │
│   │   └─▶ nba_api.stats.static.teams                       │
│   │       └─▶ (nba_api internally calls stats.nba.com)     │
│   │                                                          │
│   ├─▶ get_players()                                         │
│   │   └─▶ nba_api.stats.endpoints.commonallplayers          │
│   │       └─▶ (nba_api internally calls stats.nba.com)     │
│   │                                                          │
│   ├─▶ get_games()                                           │
│   │   └─▶ nba_api.stats.endpoints.ScoreboardV2             │
│   │       └─▶ (nba_api internally calls stats.nba.com)     │
│   │                                                          │
│   └─▶ get_box_score()                                       │
│       ├─▶ Retry logic (3 attempts)                         │
│       ├─▶ Exponential backoff                              │
│       ├─▶ Adaptive rate limiting                           │
│       └─▶ nba_api.stats.endpoints.BoxScoreTraditionalV2    │
│           └─▶ (nba_api internally calls stats.nba.com)     │
│           └─▶ Parse pandas DataFrame (itertuples)          │
│                                                              │
│ app/ingestion/nba_client.py (FALLBACK ONLY)                │
│                                                              │
│ NBAClient (Direct stats.nba.com calls - not used by default)│
│   └─▶ Only used if nba_api library not installed           │
│       └─▶ Direct requests to https://stats.nba.com/stats   │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ External NBA API (stats.nba.com)                           │
│                                                              │
│ - Rate limited                                              │
│ - Returns JSON data                                         │
│ - Accessed via nba_api Python library (NOT direct calls)   │
│                                                              │
│ Note: We use nba_api library, which internally calls       │
│ stats.nba.com but handles headers, authentication,         │
│ rate limiting, and data parsing for us.                    │
└─────────────────────────────────────────────────────────────┘
```

### Optimization Features

1. **In-Memory Duplicate Tracking**
   - Python `set` of `(game_id, player_id)` pairs
   - O(1) lookup time
   - Cleared every 200 games

2. **Batch Processing**
   - Groups 200 box scores before insert
   - Reduces database commits by 200x

3. **Smart Database Queries**
   - Large batches (>100): Skip DB duplicate check
   - Small batches (≤100): Quick DB check
   - Uses composite index for fast lookups

4. **API Resilience**
   - Retry logic (3 attempts)
   - Exponential backoff (1s, 2s, 4s)
   - Adaptive rate limiting
   - Continues on individual failures

5. **Pandas Optimization**
   - `itertuples()` instead of `iterrows()`
   - 10-100x faster DataFrame iteration

---

## File Structure

```
nba-analytics/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── db.py                   # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   │
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── players.py          # /players endpoints
│   │   ├── teams.py            # /teams endpoints
│   │   └── games.py            # /games endpoints
│   │
│   ├── ingestion/              # Data ingestion
│   │   ├── __init__.py
│   │   ├── nba_api_client.py   # NBA API client (nba_api lib)
│   │   ├── nba_client.py       # Direct API client (fallback)
│   │   ├── ingest.py           # Core ingestion logic
│   │   ├── csv_ingest.py       # CSV import utilities
│   │   └── README.md
│   │
│   └── analytics/              # Future ML/analytics
│       └── __init__.py
│
├── venv/                       # Virtual environment
├── nba_analytics.db            # SQLite database (created at runtime)
│
├── requirements.txt            # Python dependencies
├── ingest_nba_data.py          # Data ingestion entry point
├── test_games_boxscores.py     # Test script
├── test_nba_api_ingestion.py   # API ingestion test
│
└── Documentation/
    ├── README.md
    ├── DEVELOPMENT_CHECKLIST.md
    ├── OPTIMIZATION_SUMMARY.md
    ├── DUPLICATE_TRACKING_EXPLAINED.md
    └── SYSTEM_ARCHITECTURE.md  # This file
```

---

## Technology Stack

### Backend Framework
- **FastAPI**: Modern Python web framework
  - Automatic API documentation
  - Type hints and validation
  - Async support

### Database
- **SQLAlchemy**: ORM (Object-Relational Mapping)
- **SQLite**: Development database
- **PostgreSQL**: Production database (configurable)

### Data Validation
- **Pydantic**: Request/response validation
  - Type checking
  - Automatic serialization/deserialization

### Data Ingestion
- **nba-api**: Python library for NBA stats API (PRIMARY)
  - Internally calls stats.nba.com but handles all complexity
  - Handles headers, authentication, rate limiting
- **pandas**: DataFrame manipulation
- **requests**: HTTP client (fallback - only if nba_api not installed)

### Development Tools
- **Uvicorn**: ASGI server
- **Python 3.11+**: Runtime

---

## Process Flows

### 1. Application Startup

```
1. uvicorn app.main:app --reload
   │
   ▼
2. FastAPI app initialized (app/main.py)
   │
   ├─▶ Load routers (players, teams, games)
   │
   └─▶ @app.on_event("startup")
       │
       └─▶ init_db()
           │
           ├─▶ Base.metadata.create_all()
           │   └─▶ Creates all tables
           │
           └─▶ Create composite index
               └─▶ CREATE INDEX idx_box_scores_game_player
```

### 2. Data Ingestion Process

```
1. User: python ingest_nba_data.py
   │
   ▼
2. ingest_from_nba_api(season="2023-24")
   │
   ├─▶ Step 1: Fetch Teams
   │   │
   │   ├─▶ NBAAPIClient.get_teams()
   │   │   └─▶ nba_api.stats.static.teams.get_teams()
   │   │
   │   └─▶ ingest_teams() → DB
   │
   ├─▶ Step 2: Fetch Players
   │   │
   │   ├─▶ NBAAPIClient.get_players()
   │   │   └─▶ CommonAllPlayers()
   │   │
   │   └─▶ ingest_players() → DB
   │
   ├─▶ Step 3: Fetch Games
   │   │
   │   ├─▶ NBAAPIClient.get_games(season="2023-24")
   │   │   │
   │   │   ├─▶ Iterate dates: Oct 1 - Jun 30
   │   │   │
   │   │   ├─▶ ScoreboardV2(game_date=date)
   │   │   │
   │   │   └─▶ Parse game data
   │   │
   │   └─▶ ingest_game() → DB (for each game)
   │
   └─▶ Step 4: Fetch Box Scores
       │
       └─▶ For each game (1383 games):
           │
           ├─▶ NBAAPIClient.get_box_score(game_id)
           │   │
           │   ├─▶ Rate limiting (0.6-1.2s delay)
           │   │
           │   ├─▶ BoxScoreTraditionalV2(game_id)
           │   │
           │   ├─▶ Parse DataFrame (itertuples)
           │   │
           │   └─▶ Return List[BoxScoreDict]
           │
           └─▶ _batch_insert_box_scores_optimized()
               │
               ├─▶ Check memory (inserted_pairs set)
               │
               ├─▶ Check DB (if batch ≤ 100)
               │
               ├─▶ Filter duplicates
               │
               └─▶ Bulk insert (200 at a time)
```

### 3. API Request Process

```
1. Client: GET /players/123/stats?season=2023-24
   │
   ▼
2. FastAPI Router (app/routers/players.py)
   │
   ├─▶ Route: @router.get("/{player_id}/stats")
   │
   ├─▶ Dependency: get_db() → SessionLocal()
   │
   ├─▶ Query Parameter: season="2023-24"
   │
   ├─▶ Business Logic:
   │   │
   │   ├─▶ Get player
   │   │   db.query(Player).filter(id=123).first()
   │   │
   │   ├─▶ Get box scores
   │   │   db.query(BoxScore)
   │   │     .join(Game)
   │   │     .filter(
   │   │       BoxScore.player_id == 123,
   │   │       Game.season == "2023-24"
   │   │     ).all()
   │   │
   │   └─▶ Aggregate stats
   │       {
   │         "games_played": COUNT(*),
   │         "avg_points": AVG(points),
   │         "avg_rebounds": AVG(rebounds),
   │         ...
   │       }
   │
   └─▶ Response Schema (Pydantic)
       │
       └─▶ JSON Response
           {
             "player_id": 123,
             "season": "2023-24",
             "games_played": 82,
             "avg_points": 25.3,
             ...
           }
```

### 4. Duplicate Prevention Flow

```
Processing Box Score: (game_id=500, player_id=100)
   │
   ▼
1. Check In-Memory Set
   pair = (500, 100)
   if pair not in inserted_pairs:  # O(1) lookup
       │
       ├─▶ True: Add to batch
       │   batch.append(box_score)
       │   inserted_pairs.add((500, 100))
       │
       └─▶ False: Skip (already in memory)
   │
   ▼
2. Batch Reaches 200 Items
   │
   ▼
3. _batch_insert_box_scores_optimized()
   │
   ├─▶ Filter memory duplicates
   │   new_box_scores = [bs for bs in batch
   │                     if (bs.game_id, bs.player_id) not in inserted_pairs]
   │
   ├─▶ Check Batch Size
   │   │
   │   ├─▶ If > 100: Skip DB check
   │   │   existing_pairs = set()
   │   │
   │   └─▶ If ≤ 100: Query DB
   │       existing = db.query(BoxScore.game_id, BoxScore.player_id)
   │                    .filter(or_(...)).all()
   │
   ├─▶ Filter DB Duplicates
   │   final_box_scores = [bs for bs in new_box_scores
   │                      if (bs.game_id, bs.player_id) not in existing_pairs]
   │
   └─▶ Bulk Insert
       db.bulk_save_objects(final_box_scores)
       db.commit()
       │
       └─▶ Database constraint checks for duplicates
           └─▶ If duplicate: Constraint violation → Skip
```

---

## Key Design Decisions

### 1. **SQLite for Development**
- **Why**: No setup required, file-based
- **Trade-off**: Single connection, slower for high concurrency
- **Production**: Easy swap to PostgreSQL via `DATABASE_URL`

### 2. **Batch Processing**
- **Why**: Reduce database round-trips
- **Batch Size**: 200 (balance between memory and performance)
- **Result**: 99.5% fewer commits

### 3. **In-Memory Duplicate Tracking**
- **Why**: Avoid redundant database queries
- **Data Structure**: Python `set` (O(1) lookups)
- **Memory Management**: Clear every 200 games

### 4. **Smart Database Queries**
- **Why**: Large batches are usually new data
- **Strategy**: Skip DB check for batches > 100
- **Fallback**: Database unique constraint catches edge cases

### 5. **Retry Logic**
- **Why**: NBA API can be unreliable
- **Strategy**: 3 attempts with exponential backoff
- **Result**: Resilient to temporary failures

### 6. **Pandas Optimization**
- **Why**: `iterrows()` is extremely slow
- **Solution**: `itertuples()` (10-100x faster)
- **Result**: Eliminated slowdown at game 330

---

## Performance Characteristics

### Data Ingestion
- **Full Season**: ~1383 games
- **Time**: 1-2 hours
- **Box Scores**: ~20,000-30,000 entries
- **Database Queries**: ~111 (vs 41,490 naive approach)
- **Throughput**: ~10 games/minute

### API Response Times
- **Simple Queries**: <50ms
- **Aggregated Stats**: <200ms
- **List Endpoints**: <100ms (with pagination)

### Database
- **Size**: ~10-50 MB (SQLite)
- **Indexes**: All foreign keys and frequently queried columns
- **Constraints**: Unique constraints prevent duplicates

---

## Future Enhancements

### Planned Features
1. **Analytics Module** (`app/analytics/`)
   - Feature engineering
   - Playstyle embeddings
   - Similar player finding
   - Next-game prediction

2. **Caching Layer**
   - Redis for frequently accessed data
   - Cache aggregated stats

3. **Background Jobs**
   - Celery for async ingestion
   - Scheduled data updates

4. **Authentication**
   - JWT tokens
   - User management

5. **Real-time Updates**
   - WebSocket support
   - Live game updates

---

## Summary

This NBA Analytics platform is a **FastAPI-based REST API** that:
- Ingests data from the NBA API
- Stores it in a relational database (SQLite/PostgreSQL)
- Exposes RESTful endpoints for querying
- Uses optimized batch processing and duplicate prevention
- Provides automatic API documentation

The architecture is **modular**, **scalable**, and **optimized for performance**, with clear separation between data ingestion, API layer, and database operations.

