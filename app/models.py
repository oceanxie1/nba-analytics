"""SQLAlchemy models for NBA data."""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Team(Base):
    """Team model."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    abbreviation = Column(String(3), unique=True, nullable=False, index=True)
    city = Column(String, nullable=False)
    conference = Column(String, nullable=True)  # East, West
    division = Column(String, nullable=True)  # Atlantic, Central, etc.

    # Relationships
    players = relationship("Player", back_populates="team")
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")


class Player(Base):
    """Player model."""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    position = Column(String, nullable=True)  # PG, SG, SF, PF, C
    height = Column(String, nullable=True)  # e.g., "6-8"
    weight = Column(Integer, nullable=True)  # in pounds
    birth_date = Column(Date, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    box_scores = relationship("BoxScore", back_populates="player")


class Game(Base):
    """Game model."""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    game_date = Column(Date, nullable=False, index=True)
    season = Column(String, nullable=False, index=True)  # e.g., "2023-24"
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    box_scores = relationship("BoxScore", back_populates="game")


class BoxScore(Base):
    """Box score (player performance in a game) model."""
    __tablename__ = "box_scores"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    
    # Unique constraint ensures one box score per player per game
    # Also creates a composite index for fast duplicate checks
    __table_args__ = (
        UniqueConstraint('game_id', 'player_id', name='_game_player_uc'),
    )
    
    # Basic stats
    minutes = Column(Float, nullable=True)  # Minutes played
    points = Column(Integer, nullable=True, default=0)
    rebounds = Column(Integer, nullable=True, default=0)
    assists = Column(Integer, nullable=True, default=0)
    steals = Column(Integer, nullable=True, default=0)
    blocks = Column(Integer, nullable=True, default=0)
    turnovers = Column(Integer, nullable=True, default=0)
    personal_fouls = Column(Integer, nullable=True, default=0)
    
    # Shooting stats
    field_goals_made = Column(Integer, nullable=True, default=0)
    field_goals_attempted = Column(Integer, nullable=True, default=0)
    three_pointers_made = Column(Integer, nullable=True, default=0)
    three_pointers_attempted = Column(Integer, nullable=True, default=0)
    free_throws_made = Column(Integer, nullable=True, default=0)
    free_throws_attempted = Column(Integer, nullable=True, default=0)
    
    # Advanced stats (can be computed or ingested)
    plus_minus = Column(Integer, nullable=True, default=0)
    
    # Relationships
    game = relationship("Game", back_populates="box_scores")
    player = relationship("Player", back_populates="box_scores")

