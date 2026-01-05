"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime


# Team schemas
class TeamBase(BaseModel):
    name: str
    abbreviation: str = Field(..., max_length=3)
    city: str
    conference: Optional[str] = None
    division: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class Team(TeamBase):
    id: int

    class Config:
        orm_mode = True


# Player schemas
class PlayerBase(BaseModel):
    name: str
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    birth_date: Optional[date] = None
    team_id: Optional[int] = None


class PlayerCreate(PlayerBase):
    pass


class Player(PlayerBase):
    id: int
    team: Optional[Team] = None

    class Config:
        orm_mode = True


# Game schemas
class GameBase(BaseModel):
    game_date: date
    season: str
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None


class GameCreate(GameBase):
    pass


class Game(GameBase):
    id: int
    created_at: Optional[datetime] = None
    home_team: Optional[Team] = None
    away_team: Optional[Team] = None

    class Config:
        orm_mode = True


# BoxScore schemas
class BoxScoreBase(BaseModel):
    game_id: int
    player_id: int
    minutes: Optional[float] = None
    points: Optional[int] = 0
    rebounds: Optional[int] = 0
    assists: Optional[int] = 0
    steals: Optional[int] = 0
    blocks: Optional[int] = 0
    turnovers: Optional[int] = 0
    personal_fouls: Optional[int] = 0
    field_goals_made: Optional[int] = 0
    field_goals_attempted: Optional[int] = 0
    three_pointers_made: Optional[int] = 0
    three_pointers_attempted: Optional[int] = 0
    free_throws_made: Optional[int] = 0
    free_throws_attempted: Optional[int] = 0
    plus_minus: Optional[int] = 0


class BoxScoreCreate(BoxScoreBase):
    pass


class BoxScore(BoxScoreBase):
    id: int
    game: Optional[Game] = None
    player: Optional[Player] = None

    class Config:
        orm_mode = True


# Season stats schema (aggregated)
class SeasonStats(BaseModel):
    player_id: int
    player_name: str
    season: str
    games_played: int
    points_per_game: float
    rebounds_per_game: float
    assists_per_game: float
    steals_per_game: float
    blocks_per_game: float
    field_goal_percentage: Optional[float] = None
    three_point_percentage: Optional[float] = None
    free_throw_percentage: Optional[float] = None

    class Config:
        orm_mode = True


# Player features schema (comprehensive analytics)
class PlayerFeatures(BaseModel):
    player_id: int
    player_name: str
    season: Optional[str] = None
    games_played: int
    totals: Dict
    per_game: Dict
    shooting_percentages: Dict
    advanced_stats: Dict

    class Config:
        orm_mode = True


# Player comparison schemas
class ComparisonPlayer(BaseModel):
    player_id: int
    player_name: str
    team_id: Optional[int] = None
    games_played: int
    totals: Dict
    per_game: Dict
    shooting_percentages: Dict
    advanced_stats: Dict


class StatComparison(BaseModel):
    player_index: int
    player_id: int
    player_name: str
    value: float


class ComparisonDetail(BaseModel):
    best: StatComparison
    worst: StatComparison


class PlayerComparison(BaseModel):
    season: str
    players: List[ComparisonPlayer]
    comparisons: Dict[str, ComparisonDetail]

    class Config:
        orm_mode = True


# Team stats schema
class TeamStats(BaseModel):
    team_id: int
    team_name: str
    season: str
    games_played: int
    record: Dict
    totals: Dict
    per_game: Dict
    shooting_percentages: Dict
    advanced_metrics: Optional[Dict] = None
    four_factors: Optional[Dict] = None

    class Config:
        orm_mode = True


# Team comparison schemas
class ComparisonTeam(BaseModel):
    team_id: int
    team_name: str
    abbreviation: Optional[str] = None
    games_played: int
    record: Dict
    totals: Dict
    per_game: Dict
    shooting_percentages: Dict


class TeamStatComparison(BaseModel):
    team_index: int
    team_id: int
    team_name: str
    value: float


class TeamComparisonDetail(BaseModel):
    best: TeamStatComparison
    worst: TeamStatComparison


class TeamComparison(BaseModel):
    season: str
    teams: List[ComparisonTeam]
    comparisons: Dict[str, TeamComparisonDetail]

    class Config:
        orm_mode = True

