"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

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
    
    # Create composite index for faster duplicate checking in box_scores
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            # Check if index already exists
            if "sqlite" in DATABASE_URL:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name='idx_box_scores_game_player'
                """))
                if not result.fetchone():
                    conn.execute(text("""
                        CREATE INDEX idx_box_scores_game_player 
                        ON box_scores(game_id, player_id)
                    """))
                    conn.commit()
        except Exception:
            # Index might already exist or database doesn't support it
            pass

