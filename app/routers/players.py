"""Player-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from app.db import get_db
from app.models import Player, BoxScore, Game
from app.schemas import Player as PlayerSchema, PlayerCreate, SeasonStats
from app.analytics.features import calculate_season_features, calculate_career_features, calculate_rolling_averages

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/", response_model=List[PlayerSchema])
def list_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all players with optional filtering."""
    query = db.query(Player)
    
    if team_id:
        query = query.filter(Player.team_id == team_id)
    
    players = query.offset(skip).limit(limit).all()
    return players


@router.get("/{player_id}", response_model=PlayerSchema)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player by ID."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.post("/", response_model=PlayerSchema, status_code=201)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player."""
    db_player = Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


@router.get("/{player_id}/stats/{season}", response_model=SeasonStats)
def get_player_season_stats(
    player_id: int,
    season: str,
    db: Session = Depends(get_db)
):
    """Get aggregated season stats for a player."""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get all box scores for this player in this season
    box_scores = db.query(BoxScore).join(Game).filter(
        BoxScore.player_id == player_id,
        Game.season == season
    ).all()
    
    if not box_scores:
        raise HTTPException(
            status_code=404,
            detail=f"No stats found for player {player_id} in season {season}"
        )
    
    # Aggregate stats
    games_played = len(box_scores)
    total_points = sum(bs.points or 0 for bs in box_scores)
    total_rebounds = sum(bs.rebounds or 0 for bs in box_scores)
    total_assists = sum(bs.assists or 0 for bs in box_scores)
    total_steals = sum(bs.steals or 0 for bs in box_scores)
    total_blocks = sum(bs.blocks or 0 for bs in box_scores)
    
    total_fg_made = sum(bs.field_goals_made or 0 for bs in box_scores)
    total_fg_attempted = sum(bs.field_goals_attempted or 0 for bs in box_scores)
    total_3p_made = sum(bs.three_pointers_made or 0 for bs in box_scores)
    total_3p_attempted = sum(bs.three_pointers_attempted or 0 for bs in box_scores)
    total_ft_made = sum(bs.free_throws_made or 0 for bs in box_scores)
    total_ft_attempted = sum(bs.free_throws_attempted or 0 for bs in box_scores)
    
    fg_percentage = (total_fg_made / total_fg_attempted * 100) if total_fg_attempted > 0 else None
    three_point_percentage = (total_3p_made / total_3p_attempted * 100) if total_3p_attempted > 0 else None
    ft_percentage = (total_ft_made / total_ft_attempted * 100) if total_ft_attempted > 0 else None
    
    return SeasonStats(
        player_id=player_id,
        player_name=player.name,
        season=season,
        games_played=games_played,
        points_per_game=total_points / games_played,
        rebounds_per_game=total_rebounds / games_played,
        assists_per_game=total_assists / games_played,
        steals_per_game=total_steals / games_played,
        blocks_per_game=total_blocks / games_played,
        field_goal_percentage=fg_percentage,
        three_point_percentage=three_point_percentage,
        free_throw_percentage=ft_percentage
    )


@router.get("/{player_id}/features")
def get_player_features(
    player_id: int,
    season: Optional[str] = Query(None, description="Season (e.g., '2023-24'). If not provided, returns career stats."),
    db: Session = Depends(get_db)
):
    """Get comprehensive features for a player (season or career).
    
    Returns advanced stats including:
    - Per-game averages
    - Shooting percentages (FG%, 3P%, FT%, eFG%, TS%)
    - Advanced metrics (PER, Usage Rate)
    - Totals and per-game stats
    """
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if season:
        # Get season features
        features = calculate_season_features(db, player_id, season)
        if "error" in features:
            raise HTTPException(status_code=404, detail=features["error"])
        
        return {
            "player_id": player_id,
            "player_name": player.name,
            "season": season,
            **features
        }
    else:
        # Get career features
        features = calculate_career_features(db, player_id)
        if "error" in features:
            raise HTTPException(status_code=404, detail=features["error"])
        
        return {
            "player_id": player_id,
            "player_name": player.name,
            "type": "career",
            **features
        }


@router.get("/{player_id}/rolling-averages")
def get_player_rolling_averages(
    player_id: int,
    season: Optional[str] = Query(None, description="Season filter (optional)"),
    window: int = Query(5, ge=1, le=20, description="Number of games in rolling window"),
    db: Session = Depends(get_db)
):
    """Get rolling averages for a player's recent games."""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    rolling = calculate_rolling_averages(db, player_id, season=season, limit=window * 2)
    
    return {
        "player_id": player_id,
        "player_name": player.name,
        "season": season,
        "window": window,
        "rolling_averages": rolling
    }

