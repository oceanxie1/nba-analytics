"""Data ingestion functions to populate database from NBA data sources."""
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Dict, Optional
from app.db import SessionLocal
from app.models import Team, Player, Game, BoxScore
from app.ingestion.nba_client import NBAClient
from app.ingestion.nba_api_client import NBAAPIClient


def ingest_teams(teams_data: List[Dict], db: Session) -> Dict[str, int]:
    """Ingest teams into database.
    
    Args:
        teams_data: List of team dictionaries
        db: Database session
    
    Returns:
        Dictionary mapping team abbreviation to database ID
    """
    team_map = {}
    
    for team_data in teams_data:
        # Handle different data formats
        if isinstance(team_data, dict):
            abbreviation = team_data.get("abbreviation") or team_data.get("teamAbbreviation")
            name = team_data.get("name") or team_data.get("teamName")
            city = team_data.get("city") or team_data.get("teamCity", "")
        else:
            # Skip if not a dict
            continue
        
        if not abbreviation or not name:
            continue
        
        # Check if team already exists
        existing_team = db.query(Team).filter(
            Team.abbreviation == abbreviation
        ).first()
        
        if existing_team:
            team_map[abbreviation] = existing_team.id
            continue
        
        # Create new team
        team = Team(
            name=name,
            abbreviation=abbreviation,
            city=city or name.split()[-1],  # Use last word as city if not provided
            conference=team_data.get("conference"),
            division=team_data.get("division")
        )
        db.add(team)
        db.flush()  # Get ID without committing
        team_map[abbreviation] = team.id
    
    db.commit()
    return team_map


def ingest_players(players_data: List[Dict], team_map: Dict[str, int], 
                   db: Session) -> Dict[str, int]:
    """Ingest players into database.
    
    Args:
        players_data: List of player dictionaries
        team_map: Mapping of team abbreviation to team ID
        db: Database session
    
    Returns:
        Dictionary mapping player name to database ID
    """
    player_map = {}
    
    for player_data in players_data:
        if not isinstance(player_data, dict):
            continue
        
        name = player_data.get("name") or player_data.get("playerName")
        if not name:
            continue
        
        # Check if player already exists
        existing_player = db.query(Player).filter(
            Player.name == name
        ).first()
        
        if existing_player:
            player_map[name] = existing_player.id
            continue
        
        # Get team ID
        team_abbr = player_data.get("teamAbbreviation") or player_data.get("team")
        team_id = team_map.get(team_abbr) if team_abbr else None
        
        # Parse birth date if available
        birth_date = None
        if "birthDate" in player_data:
            try:
                birth_date = datetime.strptime(player_data["birthDate"], "%Y-%m-%d").date()
            except:
                pass
        
        player = Player(
            name=name,
            position=player_data.get("position"),
            height=player_data.get("height"),
            weight=player_data.get("weight"),
            birth_date=birth_date,
            team_id=team_id
        )
        db.add(player)
        db.flush()
        player_map[name] = player.id
    
    db.commit()
    return player_map


def ingest_game(game_data: Dict, team_map: Dict[str, int], 
                db: Session) -> Optional[int]:
    """Ingest a single game into database.
    
    Args:
        game_data: Game dictionary
        team_map: Mapping of team abbreviation to team ID
        db: Database session
    
    Returns:
        Game ID if successful, None otherwise
    """
    if not isinstance(game_data, dict):
        return None
    
    # Parse game date
    game_date_str = game_data.get("gameDate") or game_data.get("date")
    if not game_date_str:
        return None
    
    try:
        if isinstance(game_date_str, str):
            game_date = datetime.strptime(game_date_str.split("T")[0], "%Y-%m-%d").date()
        else:
            game_date = game_date_str
    except:
        return None
    
    # Get team IDs
    home_team_abbr = game_data.get("homeTeam") or game_data.get("homeTeamAbbreviation")
    away_team_abbr = game_data.get("awayTeam") or game_data.get("awayTeamAbbreviation")
    
    home_team_id = team_map.get(home_team_abbr) if home_team_abbr else None
    away_team_id = team_map.get(away_team_abbr) if away_team_abbr else None
    
    if not home_team_id or not away_team_id:
        return None
    
    # Check if game already exists
    existing_game = db.query(Game).filter(
        Game.game_date == game_date,
        Game.home_team_id == home_team_id,
        Game.away_team_id == away_team_id
    ).first()
    
    if existing_game:
        return existing_game.id
    
    # Determine season from date
    if game_date.month >= 10:
        season = f"{game_date.year}-{str(game_date.year + 1)[2:]}"
    else:
        season = f"{game_date.year - 1}-{str(game_date.year)[2:]}"
    
    game = Game(
        game_date=game_date,
        season=season,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_score=game_data.get("homeScore"),
        away_score=game_data.get("awayScore")
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game.id


def ingest_box_score(box_score_data: Dict, game_id: int, player_map: Dict[str, int],
                     db: Session) -> Optional[int]:
    """Ingest a box score entry.
    
    Args:
        box_score_data: Box score dictionary
        game_id: Game ID
        player_map: Mapping of player name to player ID
        db: Database session
    
    Returns:
        Box score ID if successful, None otherwise
    """
    if not isinstance(box_score_data, dict):
        return None
    
    player_name = box_score_data.get("playerName") or box_score_data.get("name")
    if not player_name:
        return None
    
    player_id = player_map.get(player_name)
    if not player_id:
        return None
    
    # Check if box score already exists
    existing = db.query(BoxScore).filter(
        BoxScore.game_id == game_id,
        BoxScore.player_id == player_id
    ).first()
    
    if existing:
        return existing.id
    
    # Parse minutes (format: "MM:SS" or float)
    minutes = box_score_data.get("minutes")
    if isinstance(minutes, str) and ":" in minutes:
        parts = minutes.split(":")
        minutes = float(parts[0]) + float(parts[1]) / 60.0
    elif minutes:
        minutes = float(minutes)
    else:
        minutes = None
    
    box_score = BoxScore(
        game_id=game_id,
        player_id=player_id,
        minutes=minutes,
        points=box_score_data.get("points") or 0,
        rebounds=box_score_data.get("rebounds") or 0,
        assists=box_score_data.get("assists") or 0,
        steals=box_score_data.get("steals") or 0,
        blocks=box_score_data.get("blocks") or 0,
        turnovers=box_score_data.get("turnovers") or 0,
        personal_fouls=box_score_data.get("personalFouls") or box_score_data.get("fouls") or 0,
        field_goals_made=box_score_data.get("fieldGoalsMade") or box_score_data.get("fgm") or 0,
        field_goals_attempted=box_score_data.get("fieldGoalsAttempted") or box_score_data.get("fga") or 0,
        three_pointers_made=box_score_data.get("threePointersMade") or box_score_data.get("fg3m") or 0,
        three_pointers_attempted=box_score_data.get("threePointersAttempted") or box_score_data.get("fg3a") or 0,
        free_throws_made=box_score_data.get("freeThrowsMade") or box_score_data.get("ftm") or 0,
        free_throws_attempted=box_score_data.get("freeThrowsAttempted") or box_score_data.get("fta") or 0,
        plus_minus=box_score_data.get("plusMinus") or box_score_data.get("plusMinus") or 0
    )
    db.add(box_score)
    db.commit()
    db.refresh(box_score)
    return box_score.id


def ingest_from_nba_api(season: str = "2023-24", db: Optional[Session] = None, use_nba_api_lib: bool = True):
    """Main function to ingest data from NBA API.
    
    Args:
        season: Season to ingest (e.g., "2023-24")
        db: Database session (creates new if None)
        use_nba_api_lib: If True, use nba_api library (recommended). If False, use direct API calls.
    """
    if db is None:
        db = SessionLocal()
    
    # Use nba_api library by default (more reliable)
    if use_nba_api_lib:
        try:
            client = NBAAPIClient()
        except ImportError:
            print("⚠️  nba_api library not installed. Install with: pip install nba-api pandas")
            print("   Falling back to direct API calls...")
            client = NBAClient()
    else:
        client = NBAClient()
    
    print(f"🏀 Starting data ingestion for season {season}...")
    
    # 1. Ingest teams
    print("📊 Fetching teams...")
    teams_data = client.get_teams(season)
    if teams_data:
        team_map = ingest_teams(teams_data, db)
        print(f"✅ Ingested {len(team_map)} teams")
    else:
        print("⚠️  No teams data found. Using manual team list...")
        # Fallback: use a basic team list
        team_map = _ingest_basic_teams(db)
    
    # 2. Ingest players
    print("👥 Fetching players...")
    players_data = client.get_players(season)
    if players_data:
        player_map = ingest_players(players_data, team_map, db)
        print(f"✅ Ingested {len(player_map)} players")
    else:
        print("⚠️  No players data found")
        player_map = {}
    
    # 3. Ingest games (this might be limited by API)
    print("🏀 Fetching games...")
    games_data = client.get_games(season)
    if games_data:
        game_count = 0
        for game_data in games_data:
            game_id = ingest_game(game_data, team_map, db)
            if game_id:
                game_count += 1
        print(f"✅ Ingested {game_count} games")
    else:
        print("⚠️  No games data found")
    
    print("✅ Data ingestion complete!")
    
    if db != SessionLocal():
        db.close()


def _ingest_basic_teams(db: Session) -> Dict[str, int]:
    """Fallback: ingest basic NBA teams if API fails."""
    basic_teams = [
        {"name": "Los Angeles Lakers", "abbreviation": "LAL", "city": "Los Angeles", "conference": "West", "division": "Pacific"},
        {"name": "Golden State Warriors", "abbreviation": "GSW", "city": "San Francisco", "conference": "West", "division": "Pacific"},
        {"name": "Boston Celtics", "abbreviation": "BOS", "city": "Boston", "conference": "East", "division": "Atlantic"},
        {"name": "Miami Heat", "abbreviation": "MIA", "city": "Miami", "conference": "East", "division": "Southeast"},
        {"name": "Denver Nuggets", "abbreviation": "DEN", "city": "Denver", "conference": "West", "division": "Northwest"},
    ]
    return ingest_teams(basic_teams, db)

