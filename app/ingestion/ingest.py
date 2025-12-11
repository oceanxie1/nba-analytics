"""Data ingestion functions to populate database from NBA data sources."""
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Dict, Optional
from sqlalchemy import and_
from app.db import SessionLocal
from app.models import Team, Player, Game, BoxScore
from app.ingestion.nba_client import NBAClient
from app.ingestion.nba_api_client import NBAAPIClient
from datetime import datetime


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
    
    # Parse minutes (format: "MM:SS", float, or other formats)
    minutes = box_score_data.get("minutes")
    if isinstance(minutes, str):
        if ":" in minutes:
            # Format: "MM:SS"
            try:
                parts = minutes.split(":")
                if len(parts) == 2:
                    minutes = float(parts[0]) + float(parts[1]) / 60.0
                else:
                    minutes = None
            except (ValueError, IndexError):
                minutes = None
        elif minutes.replace(".", "").replace("-", "").isdigit():
            # Try to parse as float if it's numeric
            try:
                minutes = float(minutes)
            except ValueError:
                minutes = None
        else:
            # Invalid format (like "0-57" or other non-standard)
            minutes = None
    elif minutes is not None:
        try:
            minutes = float(minutes)
        except (ValueError, TypeError):
            minutes = None
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


def _create_box_score_object(box_score_data: Dict, game_id: int, player_map: Dict[str, int],
                            db: Session) -> Optional[BoxScore]:
    """Create a BoxScore object without committing (for batch processing).
    
    Returns:
        BoxScore object if valid, None otherwise
    """
    if not isinstance(box_score_data, dict):
        return None
    
    # Fast lookup - try playerName first (most common)
    player_name = box_score_data.get("playerName")
    if not player_name:
        player_name = box_score_data.get("name")
    if not player_name:
        return None
    
    # Fast dictionary lookup
    player_id = player_map.get(player_name)
    if not player_id:
        return None
    
    # Parse minutes
    minutes = box_score_data.get("minutes")
    if isinstance(minutes, str):
        if ":" in minutes:
            try:
                parts = minutes.split(":")
                if len(parts) == 2:
                    minutes = float(parts[0]) + float(parts[1]) / 60.0
                else:
                    minutes = None
            except (ValueError, IndexError):
                minutes = None
        elif minutes.replace(".", "").replace("-", "").isdigit():
            try:
                minutes = float(minutes)
            except ValueError:
                minutes = None
        else:
            minutes = None
    elif minutes is not None:
        try:
            minutes = float(minutes)
        except (ValueError, TypeError):
            minutes = None
    else:
        minutes = None
    
    return BoxScore(
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


def _batch_insert_box_scores_optimized(box_scores: List[BoxScore], db: Session, inserted_pairs: set) -> int:
    """Optimized batch insert with minimal duplicate checking.
    
    Args:
        box_scores: List of BoxScore objects to insert
        db: Database session
        inserted_pairs: Set of (game_id, player_id) pairs already inserted (updated in place)
    
    Returns:
        Number of box scores actually inserted
    """
    if not box_scores:
        return 0
    
    # Filter out pairs we've already inserted in this session
    new_box_scores = [
        bs for bs in box_scores
        if (bs.game_id, bs.player_id) not in inserted_pairs
    ]
    
    if not new_box_scores:
        return 0
    
    # Skip database duplicate check if we have many pairs (assume they're new)
    # Only check DB if we have a small batch (likely duplicates from retry)
    pairs_to_check = {(bs.game_id, bs.player_id) for bs in new_box_scores}
    
    if len(pairs_to_check) > 100:
        # Large batch - assume most are new, skip expensive DB query
        # The in-memory tracking should catch most duplicates
        existing_pairs = set()
    else:
        # Small batch - do quick DB check (might be retrying duplicates)
        from sqlalchemy import text, or_, and_
        conditions = [
            and_(BoxScore.game_id == gid, BoxScore.player_id == pid)
            for gid, pid in pairs_to_check
        ]
        
        if conditions:
            existing = db.query(BoxScore.game_id, BoxScore.player_id).filter(
                or_(*conditions)
            ).all()
            existing_pairs = {(e[0], e[1]) for e in existing}
        else:
            existing_pairs = set()
    
    # Filter out database duplicates
    final_box_scores = [
        bs for bs in new_box_scores
        if (bs.game_id, bs.player_id) not in existing_pairs
    ]
    
    if not final_box_scores:
        return 0
    
    # Update inserted_pairs with what we're about to insert
    for bs in final_box_scores:
        inserted_pairs.add((bs.game_id, bs.player_id))
    
    inserted_count = 0
    if final_box_scores:
        try:
            # Use bulk_save_objects for speed
            db.bulk_save_objects(final_box_scores, update_changed_only=False)
            db.commit()
            inserted_count = len(final_box_scores)
        except Exception as e:
            # If bulk fails (e.g., duplicate constraint), try individual with ignore
            db.rollback()
            from sqlalchemy import text
            for bs in final_box_scores:
                try:
                    # Try bulk insert first, fall back to individual
                    db.add(bs)
                    db.commit()
                    inserted_pairs.add((bs.game_id, bs.player_id))
                    inserted_count += 1
                except Exception:
                    # Duplicate or other error - skip this one
                    db.rollback()
                    # Remove from inserted_pairs if it failed
                    inserted_pairs.discard((bs.game_id, bs.player_id))
                    continue
    
    return inserted_count


def _batch_insert_box_scores(box_scores: List[BoxScore], db: Session):
    """Legacy batch insert function (kept for compatibility)."""
    inserted_pairs = set()
    _batch_insert_box_scores_optimized(box_scores, db, inserted_pairs)


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
    
    # 3. Ingest games for entire season
    print("🏀 Fetching games for season...")
    games_data = client.get_games(season, game_date="season")
    if games_data:
        game_count = 0
        game_id_map = {}  # Map NBA game ID to our database game ID
        
        for game_data in games_data:
            db_game_id = ingest_game(game_data, team_map, db)
            if db_game_id:
                game_count += 1
                nba_game_id = game_data.get("gameId")
                if nba_game_id:
                    game_id_map[nba_game_id] = db_game_id
        
        print(f"✅ Ingested {game_count} games")
        
        # 4. Ingest box scores for all games (optimized with batch processing)
        if game_id_map and player_map:
            print("📊 Fetching box scores...")
            box_score_count = 0
            total_games = len(game_id_map)
            batch_size = 200  # Increased batch size for better performance
            batch = []
            inserted_pairs = set()  # Track what we've inserted in this session
            
            import time as time_module
            for idx, (nba_game_id, db_game_id) in enumerate(game_id_map.items(), 1):
                if idx % 10 == 0:
                    print(f"   Progress: {idx}/{total_games} games processed ({box_score_count} box scores so far)...")
                
                # Time the API call to see if that's the bottleneck
                api_start = time_module.time()
                box_scores_data = client.get_box_score(nba_game_id)
                api_time = time_module.time() - api_start
                
                # Note: Slow API warnings are now handled inside get_box_score() with retry logic
                for box_score_data in box_scores_data:
                    box_score_obj = _create_box_score_object(box_score_data, db_game_id, player_map, db)
                    if box_score_obj:
                        # Skip if we've already inserted this pair in this session
                        pair = (box_score_obj.game_id, box_score_obj.player_id)
                        if pair not in inserted_pairs:
                            batch.append(box_score_obj)
                            inserted_pairs.add(pair)
                            
                            # Batch commit for performance
                            if len(batch) >= batch_size:
                                db_start = time_module.time()
                                inserted = _batch_insert_box_scores_optimized(batch, db, inserted_pairs)
                                db_time = time_module.time() - db_start
                                box_score_count += inserted  # Count only actually inserted
                                
                                # Warn if DB operation is slow
                                if db_time > 1.0 and idx % 50 == 0:
                                    print(f"   ⚠️  Slow DB operation: {db_time:.2f}s for batch at game {idx}")
                                
                                batch = []
                
                # Periodically clear inserted_pairs to free memory and reduce lookup time
                # Clear more frequently to keep set size manageable
                if idx % 200 == 0:
                    # Before clearing, commit any pending batch
                    if batch:
                        inserted = _batch_insert_box_scores_optimized(batch, db, inserted_pairs)
                        box_score_count += inserted  # Count only actually inserted
                        batch = []
                    # Clear to reduce memory and lookup overhead
                    inserted_pairs.clear()
                    print(f"   Cleared memory cache at game {idx}")
            
            # Commit remaining box scores
            if batch:
                inserted = _batch_insert_box_scores_optimized(batch, db, inserted_pairs)
                box_score_count += inserted  # Count only actually inserted
            
            print(f"✅ Ingested {box_score_count} box score entries")
        else:
            print("⚠️  Skipping box scores (no games or players found)")
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

