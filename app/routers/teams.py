"""Team-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models import Team, Game
from app.schemas import Team as TeamSchema, TeamCreate, Game as GameSchema, TeamComparison
from app.analytics.team_features import calculate_team_season_stats, calculate_game_team_stats, compare_teams
from app.cache import cache_manager, cache_key_team_stats, cache_key_team_comparison, cache_stats
import time

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=List[TeamSchema])
def list_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all teams."""
    teams = db.query(Team).offset(skip).limit(limit).all()
    return teams


@router.get("/compare", response_model=TeamComparison)
def compare_teams_endpoint(
    team_ids: str = Query(..., description="Comma-separated list of team IDs (e.g., '1,2')"),
    season: str = Query(..., description="Season (e.g., '2023-24')"),
    db: Session = Depends(get_db)
):
    """Compare multiple teams side-by-side for a given season.
    
    Returns comprehensive stats for each team including:
    - Win/loss record (overall, home, away)
    - Per-game averages (points, rebounds, assists, etc.)
    - Shooting percentages (FG%, 3P%, FT%, eFG%, TS%)
    - Comparisons highlighting best/worst performers for each stat
    
    Example:
        GET /teams/compare?team_ids=1,2&season=2023-24
    """
    # Parse team IDs
    try:
        team_id_list = [int(tid.strip()) for tid in team_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid team_ids format. Expected comma-separated integers (e.g., '1,2')"
        )
    
    if len(team_id_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 team IDs are required for comparison"
        )
    
    if len(team_id_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 teams can be compared at once"
        )
    
    # Check cache first
    cache_key = cache_key_team_comparison(team_id_list, season)
    cache_lookup_start = time.time()
    cached_result = cache_manager.get(cache_key)
    cache_lookup_time = time.time() - cache_lookup_start
    
    if cached_result is not None:
        cache_stats.record_hit(cache_lookup_time)
        return cached_result
    
    # Cache miss - need to query database
    db_query_start = time.time()
    
    # Get comparison data
    comparison_result = compare_teams(db, team_id_list, season)
    
    if "error" in comparison_result:
        raise HTTPException(status_code=404, detail=comparison_result["error"])
    
    # Cache the result (1 hour TTL)
    cache_manager.set(cache_key, comparison_result, ttl=3600)
    
    # Record cache miss response time
    db_query_time = time.time() - db_query_start
    cache_stats.record_miss(db_query_time)
    
    return comparison_result


@router.get("/{team_id}", response_model=TeamSchema)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get a specific team by ID."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/", response_model=TeamSchema, status_code=201)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """Create a new team."""
    db_team = Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.get("/{team_id}/stats/{season}")
def get_team_season_stats(
    team_id: int,
    season: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive season stats for a team.
    
    Returns:
    - Win/loss record (overall, home, away)
    - Per-game averages (points, rebounds, assists, etc.)
    - Shooting percentages (FG%, 3P%, FT%, eFG%, TS%)
    - Advanced metrics (Pace, Offensive/Defensive Rating, Net Rating)
    - Four Factors (eFG%, TOV%, FTA Rate)
    - Totals for the season
    
    Results are cached for 1 hour to improve performance.
    """
    # Check cache first
    cache_key = cache_key_team_stats(team_id, season)
    cache_lookup_start = time.time()
    cached_result = cache_manager.get(cache_key)
    cache_lookup_time = time.time() - cache_lookup_start
    
    if cached_result is not None:
        cache_stats.record_hit(cache_lookup_time)
        return cached_result
    
    # Cache miss - need to query database
    db_query_start = time.time()
    
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team season stats
    stats = calculate_team_season_stats(db, team_id, season)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    
    result = {
        "team_id": team_id,
        "team_name": team.name,
        **stats
    }
    
    # Cache the result (1 hour TTL)
    cache_manager.set(cache_key, result, ttl=3600)
    
    # Record cache miss response time
    db_query_time = time.time() - db_query_start
    cache_stats.record_miss(db_query_time)
    
    return result


@router.get("/{team_id}/games", response_model=List[GameSchema])
def get_team_games(
    team_id: int,
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023-24')"),
    db: Session = Depends(get_db)
):
    """Get all games for a team, optionally filtered by season."""
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get games where team is home or away
    query = db.query(Game).filter(
        (Game.home_team_id == team_id) | (Game.away_team_id == team_id)
    )
    
    if season:
        query = query.filter(Game.season == season)
    
    games = query.order_by(Game.game_date).all()
    return games


@router.get("/{team_id}/games/{game_id}/stats")
def get_team_game_stats(
    team_id: int,
    game_id: int,
    db: Session = Depends(get_db)
):
    """Get team stats for a specific game."""
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get game team stats
    stats = calculate_game_team_stats(db, game_id, team_id)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    
    return {
        "team_id": team_id,
        "team_name": team.name,
        **stats
    }

