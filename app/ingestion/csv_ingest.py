"""CSV-based data ingestion as an alternative to API."""
import csv
from typing import List, Dict
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.ingestion.ingest import ingest_teams, ingest_players, ingest_game, ingest_box_score


def ingest_teams_from_csv(csv_path: str, db: Session) -> Dict[str, int]:
    """Ingest teams from CSV file.
    
    CSV format: name,abbreviation,city,conference,division
    Example: Los Angeles Lakers,LAL,Los Angeles,West,Pacific
    """
    teams_data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams_data.append({
                "name": row.get("name", "").strip(),
                "abbreviation": row.get("abbreviation", "").strip(),
                "city": row.get("city", "").strip(),
                "conference": row.get("conference", "").strip() or None,
                "division": row.get("division", "").strip() or None
            })
    return ingest_teams(teams_data, db)


def ingest_players_from_csv(csv_path: str, team_map: Dict[str, int], 
                           db: Session) -> Dict[str, int]:
    """Ingest players from CSV file.
    
    CSV format: name,position,height,weight,birth_date,team_abbreviation
    Example: LeBron James,SF,6-9,250,1984-12-30,LAL
    """
    players_data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            players_data.append({
                "name": row.get("name", "").strip(),
                "position": row.get("position", "").strip() or None,
                "height": row.get("height", "").strip() or None,
                "weight": int(row["weight"]) if row.get("weight") else None,
                "birthDate": row.get("birth_date", "").strip() or None,
                "teamAbbreviation": row.get("team_abbreviation", "").strip()
            })
    return ingest_players(players_data, team_map, db)


def ingest_games_from_csv(csv_path: str, team_map: Dict[str, int],
                          db: Session) -> List[int]:
    """Ingest games from CSV file.
    
    CSV format: game_date,season,home_team,away_team,home_score,away_score
    Example: 2024-01-15,2023-24,LAL,GSW,120,115
    """
    game_ids = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_data = {
                "gameDate": row.get("game_date", "").strip(),
                "homeTeam": row.get("home_team", "").strip(),
                "awayTeam": row.get("away_team", "").strip(),
                "homeScore": int(row["home_score"]) if row.get("home_score") else None,
                "awayScore": int(row["away_score"]) if row.get("away_score") else None
            }
            game_id = ingest_game(game_data, team_map, db)
            if game_id:
                game_ids.append(game_id)
    return game_ids


def ingest_box_scores_from_csv(csv_path: str, player_map: Dict[str, int],
                               db: Session) -> List[int]:
    """Ingest box scores from CSV file.
    
    CSV format: game_id,player_name,minutes,points,rebounds,assists,steals,blocks,
                turnovers,personal_fouls,fgm,fga,fg3m,fg3a,ftm,fta,plus_minus
    """
    box_score_ids = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            box_score_data = {
                "playerName": row.get("player_name", "").strip(),
                "minutes": row.get("minutes", "").strip() or None,
                "points": int(row["points"]) if row.get("points") else 0,
                "rebounds": int(row["rebounds"]) if row.get("rebounds") else 0,
                "assists": int(row["assists"]) if row.get("assists") else 0,
                "steals": int(row["steals"]) if row.get("steals") else 0,
                "blocks": int(row["blocks"]) if row.get("blocks") else 0,
                "turnovers": int(row["turnovers"]) if row.get("turnovers") else 0,
                "personalFouls": int(row["personal_fouls"]) if row.get("personal_fouls") else 0,
                "fieldGoalsMade": int(row["fgm"]) if row.get("fgm") else 0,
                "fieldGoalsAttempted": int(row["fga"]) if row.get("fga") else 0,
                "threePointersMade": int(row["fg3m"]) if row.get("fg3m") else 0,
                "threePointersAttempted": int(row["fg3a"]) if row.get("fg3a") else 0,
                "freeThrowsMade": int(row["ftm"]) if row.get("ftm") else 0,
                "freeThrowsAttempted": int(row["fta"]) if row.get("fta") else 0,
                "plusMinus": int(row["plus_minus"]) if row.get("plus_minus") else 0
            }
            game_id = int(row["game_id"])
            box_score_id = ingest_box_score(box_score_data, game_id, player_map, db)
            if box_score_id:
                box_score_ids.append(box_score_id)
    return box_score_ids

