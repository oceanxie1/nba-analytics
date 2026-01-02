"""Game and box score related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from app.db import get_db
from app.models import Game, BoxScore
from app.schemas import Game as GameSchema, GameCreate, BoxScore as BoxScoreSchema, BoxScoreCreate
from app.analytics.team_features import calculate_game_team_stats

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/", response_model=GameSchema, status_code=201)
def create_game(game: GameCreate, db: Session = Depends(get_db)):
    """Create a new game."""
    db_game = Game(**game.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


@router.get("/{game_id}", response_model=GameSchema)
def get_game(game_id: int, db: Session = Depends(get_db)):
    """Get a specific game by ID."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post("/box-scores", response_model=BoxScoreSchema, status_code=201)
def create_box_score(box_score: BoxScoreCreate, db: Session = Depends(get_db)):
    """Create a new box score entry (by box score payload, not game ID)."""
    db_box_score = BoxScore(**box_score.dict())
    db.add(db_box_score)
    db.commit()
    db.refresh(db_box_score)
    return db_box_score


@router.get("/box-scores/{box_score_id}", response_model=BoxScoreSchema)
def get_box_score(box_score_id: int, db: Session = Depends(get_db)):
    """Get a specific box score by ID."""
    box_score = db.query(BoxScore).filter(BoxScore.id == box_score_id).first()
    if not box_score:
        raise HTTPException(status_code=404, detail="Box score not found")
    return box_score


@router.get("/{game_id}/box-scores", response_model=List[BoxScoreSchema])
def get_box_scores_for_game(game_id: int, db: Session = Depends(get_db)):
    """Get all box scores for a specific game."""
    # We intentionally return an empty list (200) if there are no box scores yet
    # instead of a 404, so clients can distinguish "no data" from "bad route".
    box_scores = db.query(BoxScore).filter(BoxScore.game_id == game_id).all()
    return box_scores


@router.get("/{game_id}/team-stats")
def get_game_team_stats(game_id: int, db: Session = Depends(get_db)):
    """Get team stats for both teams in a game.
    
    Returns stats for both home and away teams, including:
    - Points, rebounds, assists, etc.
    - Shooting percentages
    - Game result (win/loss)
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    home_stats = calculate_game_team_stats(db, game_id, game.home_team_id)
    away_stats = calculate_game_team_stats(db, game_id, game.away_team_id)
    
    if "error" in home_stats or "error" in away_stats:
        raise HTTPException(
            status_code=404,
            detail="Team stats not available for this game"
        )
    
    return {
        "game_id": game_id,
        "game_date": game.game_date.isoformat(),
        "season": game.season,
        "home_team": {
            "team_id": game.home_team_id,
            "team_name": game.home_team.name if game.home_team else None,
            **home_stats
        },
        "away_team": {
            "team_id": game.away_team_id,
            "team_name": game.away_team.name if game.away_team else None,
            **away_stats
        }
    }


@router.get("/{game_id}/summary")
def get_game_summary(game_id: int, db: Session = Depends(get_db)):
    """Get a comprehensive game summary including game info, team stats, and box scores."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get team stats
    home_stats = calculate_game_team_stats(db, game_id, game.home_team_id)
    away_stats = calculate_game_team_stats(db, game_id, game.away_team_id)
    
    # Get box scores
    box_scores = db.query(BoxScore).filter(BoxScore.game_id == game_id).all()
    
    return {
        "game": {
            "id": game.id,
            "date": game.game_date.isoformat(),
            "season": game.season,
            "home_team": {
                "id": game.home_team_id,
                "name": game.home_team.name if game.home_team else None,
                "score": game.home_score
            },
            "away_team": {
                "id": game.away_team_id,
                "name": game.away_team.name if game.away_team else None,
                "score": game.away_score
            }
        },
        "team_stats": {
            "home": home_stats if "error" not in home_stats else None,
            "away": away_stats if "error" not in away_stats else None
        },
        "box_scores": [
            {
                "id": bs.id,
                "player_id": bs.player_id,
                "player_name": bs.player.name if bs.player else None,
                "points": bs.points,
                "rebounds": bs.rebounds,
                "assists": bs.assists,
                "minutes": bs.minutes
            }
            for bs in box_scores
        ],
        "box_score_count": len(box_scores)
    }

