"""Team-related API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import Team
from app.schemas import Team as TeamSchema, TeamCreate

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

