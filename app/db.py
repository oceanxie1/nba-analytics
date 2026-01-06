"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# SQLite for development, easy to swap to Postgres later
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nba_analytics.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables and indexes."""
    Base.metadata.create_all(bind=engine)
    
    # Create indexes for common query patterns
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            if "sqlite" in DATABASE_URL:
                # Check and create indexes one by one
                indexes = [
                    # Composite index for box_scores (game_id, player_id) - already exists via UniqueConstraint
                    # but we'll create it explicitly for clarity
                    ("idx_box_scores_game_player", """
                        CREATE INDEX IF NOT EXISTS idx_box_scores_game_player 
                        ON box_scores(game_id, player_id)
                    """),
                    
                    # Index for BoxScore queries filtered by player_id (common in analytics)
                    ("idx_box_scores_player_id", """
                        CREATE INDEX IF NOT EXISTS idx_box_scores_player_id 
                        ON box_scores(player_id)
                    """),
                    
                    # Composite index for Game queries filtered by season + home_team_id
                    ("idx_games_season_home_team", """
                        CREATE INDEX IF NOT EXISTS idx_games_season_home_team 
                        ON games(season, home_team_id)
                    """),
                    
                    # Composite index for Game queries filtered by season + away_team_id
                    ("idx_games_season_away_team", """
                        CREATE INDEX IF NOT EXISTS idx_games_season_away_team 
                        ON games(season, away_team_id)
                    """),
                    
                    # Index for Player queries filtered by team_id
                    ("idx_players_team_id", """
                        CREATE INDEX IF NOT EXISTS idx_players_team_id 
                        ON players(team_id)
                    """),
                    
                    # Index for Game queries filtered by game_date (for sorting)
                    ("idx_games_game_date", """
                        CREATE INDEX IF NOT EXISTS idx_games_game_date 
                        ON games(game_date)
                    """),
                ]
                
                for index_name, create_sql in indexes:
                    # Check if index exists
                    result = conn.execute(text(f"""
                        SELECT name FROM sqlite_master 
                        WHERE type='index' AND name='{index_name}'
                    """))
                    if not result.fetchone():
                        conn.execute(text(create_sql))
                        conn.commit()
                        logger.info(f"Created index: {index_name}")
        except Exception as e:
            # Index might already exist or database doesn't support it
            logger.warning(f"Error creating indexes: {e}")
            pass

