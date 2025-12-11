"""Game and box score related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import Game, BoxScore
from app.schemas import Game as GameSchema, GameCreate, BoxScore as BoxScoreSchema, BoxScoreCreate

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
    """Create a new box score entry."""
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

