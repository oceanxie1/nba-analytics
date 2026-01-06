"""Player-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from app.db import get_db
from app.models import Player, BoxScore, Game
from app.schemas import Player as PlayerSchema, PlayerCreate, SeasonStats, PlayerComparison
from app.analytics.features import (
    calculate_season_features, calculate_career_features, calculate_rolling_averages, compare_players,
    calculate_performance_vs_team, calculate_performance_by_game_situation, calculate_performance_by_period
)
from app.cache import cache_manager, cache_key_player_features, cache_key_player_comparison, cache_stats
import time

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


@router.get("/compare", response_model=PlayerComparison)
def compare_players_endpoint(
    player_ids: str = Query(..., description="Comma-separated list of player IDs (e.g., '1,2,3')"),
    season: str = Query(..., description="Season (e.g., '2023-24')"),
    db: Session = Depends(get_db)
):
    """Compare multiple players side-by-side for a given season.
    
    Returns comprehensive stats for each player including:
    - Per-game averages (points, rebounds, assists, etc.)
    - Shooting percentages (FG%, 3P%, FT%, eFG%, TS%)
    - Advanced stats (PER, Usage Rate)
    - Comparisons highlighting best/worst performers for each stat
    
    Example:
        GET /players/compare?player_ids=1,2,3&season=2023-24
    """
    # Parse player IDs
    try:
        player_id_list = [int(pid.strip()) for pid in player_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid player_ids format. Expected comma-separated integers (e.g., '1,2,3')"
        )
    
    if len(player_id_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 player IDs are required for comparison"
        )
    
    if len(player_id_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 players can be compared at once"
        )
    
    # Check cache first
    cache_key = cache_key_player_comparison(player_id_list, season)
    cache_lookup_start = time.time()
    cached_result = cache_manager.get(cache_key)
    cache_lookup_time = time.time() - cache_lookup_start
    
    if cached_result is not None:
        cache_stats.record_hit(cache_lookup_time)
        return cached_result
    
    # Cache miss - need to query database
    db_query_start = time.time()
    
    # Get comparison data
    comparison_result = compare_players(db, player_id_list, season)
    
    if "error" in comparison_result:
        raise HTTPException(status_code=404, detail=comparison_result["error"])
    
    # Cache the result (1 hour TTL)
    cache_manager.set(cache_key, comparison_result, ttl=3600)
    
    # Record cache miss response time
    db_query_time = time.time() - db_query_start
    cache_stats.record_miss(db_query_time)
    
    return comparison_result


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
    - Advanced metrics (PER, Usage Rate, BPM, VORP, Win Shares)
    - Clutch stats
    - Totals and per-game stats
    
    Results are cached for 1 hour to improve performance.
    """
    # Check cache first
    cache_key = cache_key_player_features(player_id, season)
    cache_lookup_start = time.time()
    cached_result = cache_manager.get(cache_key)
    cache_lookup_time = time.time() - cache_lookup_start
    
    if cached_result is not None:
        # Cache hit - very fast (just Redis lookup + JSON parse)
        cache_stats.record_hit(cache_lookup_time)
        return cached_result
    
    # Cache miss - need to query database and calculate
    db_query_start = time.time()
    
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if season:
        # Get season features
        features = calculate_season_features(db, player_id, season)
        if "error" in features:
            raise HTTPException(status_code=404, detail=features["error"])
        
        result = {
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
        
        result = {
            "player_id": player_id,
            "player_name": player.name,
            "type": "career",
            **features
        }
    
    # Cache the result (1 hour TTL)
    cache_set_start = time.time()
    cache_success = cache_manager.set(cache_key, result, ttl=3600)
    cache_set_time = time.time() - cache_set_start
    if not cache_success and cache_manager.enabled:
        # Log warning if cache failed but should be enabled
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to cache result for key: {cache_key}")
    
    # Record cache miss response time (DB query + calculation time, excluding cache set)
    db_query_time = time.time() - db_query_start
    cache_stats.record_miss(db_query_time)
    
    return result


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


@router.get("/{player_id}/contextual/vs-team")
def get_performance_vs_team(
    player_id: int,
    opponent_team_id: int = Query(..., description="Opponent team ID"),
    season: Optional[str] = Query(None, description="Season filter (optional)"),
    db: Session = Depends(get_db)
):
    """Get player performance against a specific team."""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Verify team exists
    from app.models import Team
    team = db.query(Team).filter(Team.id == opponent_team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    stats = calculate_performance_vs_team(db, player_id, opponent_team_id, season=season)
    
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    
    return {
        "player_id": player_id,
        "player_name": player.name,
        "opponent_team_id": opponent_team_id,
        "opponent_team_name": team.name,
        "season": season,
        "stats": stats
    }


@router.get("/{player_id}/contextual/game-situation")
def get_performance_by_game_situation(
    player_id: int,
    season: Optional[str] = Query(None, description="Season filter (optional)"),
    db: Session = Depends(get_db)
):
    """Get player performance in different game situations (close games vs blowouts)."""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    stats = calculate_performance_by_game_situation(db, player_id, season=season)
    
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    
    return {
        "player_id": player_id,
        "player_name": player.name,
        "season": season,
        "game_situations": stats
    }


@router.get("/{player_id}/contextual/by-period")
def get_performance_by_period(
    player_id: int,
    season: Optional[str] = Query(None, description="Season filter (optional)"),
    db: Session = Depends(get_db)
):
    """Get player performance by month/period of season."""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    stats = calculate_performance_by_period(db, player_id, season=season)
    
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    
    return {
        "player_id": player_id,
        "player_name": player.name,
        "season": season,
        "monthly_performance": stats
    }

