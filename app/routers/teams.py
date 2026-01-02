"""Team-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models import Team, Game
from app.schemas import Team as TeamSchema, TeamCreate, Game as GameSchema
from app.analytics.team_features import calculate_team_season_stats, calculate_game_team_stats

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=List[TeamSchema])
def list_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all teams."""
    teams = db.query(Team).offset(skip).limit(limit).all()
    return teams


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
    - Totals for the season
    """
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team season stats
    stats = calculate_team_season_stats(db, team_id, season)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    
    return {
        "team_id": team_id,
        "team_name": team.name,
        **stats
    }


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

