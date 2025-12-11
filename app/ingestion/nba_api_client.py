"""NBA API client using the nba_api Python library (recommended)."""
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from nba_api.stats.endpoints import (
    commonallplayers,
    commonteamyears,
    ScoreboardV2,
    BoxScoreTraditionalV2,
    playergamelog
)
from nba_api.stats.static import teams, players
import time


class NBAAPIClient:
    """Client using the nba_api library (more reliable than direct API calls)."""
    
    def __init__(self, rate_limit_delay: float = 0.6):
        """Initialize NBA API client.
        
        Args:
            rate_limit_delay: Seconds to wait between API calls
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_teams(self, season: Optional[str] = None) -> List[Dict]:
        """Fetch all NBA teams.
        
        Args:
            season: Season year (e.g., "2023-24"). If None, uses current season.
        
        Returns:
            List of team dictionaries
        """
        self._rate_limit()
        
        try:
            # Get teams from static data (more reliable)
            nba_teams = teams.get_teams()
            
            # Convert to our format
            teams_data = []
            for team in nba_teams:
                teams_data.append({
                    "name": team["full_name"],
                    "abbreviation": team["abbreviation"],
                    "city": team["city"],
                    "conference": None,  # Not in static data, would need to map
                    "division": None    # Not in static data, would need to map
                })
            
            return teams_data
        except Exception as e:
            print(f"Error fetching teams: {e}")
            return []
    
    def get_players(self, season: Optional[str] = None, 
                   team_id: Optional[int] = None) -> List[Dict]:
        """Fetch players.
        
        Args:
            season: Season year (e.g., "2023-24")
            team_id: Optional team ID to filter players
        
        Returns:
            List of player dictionaries
        """
        self._rate_limit()
        
        if not season:
            current_year = datetime.now().year
            if datetime.now().month >= 10:
                season = f"{current_year}-{str(current_year + 1)[2:]}"
            else:
                season = f"{current_year - 1}-{str(current_year)[2:]}"
        
        try:
            # Get all players for the season
            if team_id:
                # Filter by team (would need team_id mapping)
                all_players = commonallplayers.CommonAllPlayers(
                    is_only_current_season=1,
                    league_id='00',
                    season=season
                )
            else:
                all_players = commonallplayers.CommonAllPlayers(
                    is_only_current_season=1,
                    league_id='00',
                    season=season
                )
            
            df = all_players.get_data_frames()[0]
            
            # Convert DataFrame to list of dicts
            players_data = []
            for _, row in df.iterrows():
                players_data.append({
                    "name": row.get("DISPLAY_FIRST_LAST", ""),
                    "playerId": row.get("PERSON_ID"),
                    "teamAbbreviation": row.get("TEAM_ABBREVIATION", ""),
                    "position": None,  # Would need additional call
                    "height": None,    # Would need additional call
                    "weight": None     # Would need additional call
                })
            
            return players_data
        except Exception as e:
            print(f"Error fetching players: {e}")
            return []
    
    def get_games(self, season: str, game_date: Optional[str] = None) -> List[Dict]:
        """Fetch games for a date or season.
        
        Args:
            season: Season year (e.g., "2023-24")
            game_date: Specific date (YYYY-MM-DD). If None, gets today's games.
        
        Returns:
            List of game dictionaries
        """
        self._rate_limit()
        
        try:
            if game_date:
                # Parse date
                date_obj = datetime.strptime(game_date, "%Y-%m-%d")
                game_date_str = date_obj.strftime("%m/%d/%Y")
            else:
                # Today's games
                game_date_str = datetime.now().strftime("%m/%d/%Y")
            
            scoreboard_data = ScoreboardV2(game_date=game_date_str)
            games_dict = scoreboard_data.get_dict()
            
            games_data = []
            for game in games_dict.get("resultSets", [{}])[0].get("rowSet", []):
                # Parse game data (structure varies)
                games_data.append({
                    "gameId": game[0] if len(game) > 0 else None,
                    "gameDate": game_date,
                    "homeTeam": game[6] if len(game) > 6 else None,
                    "awayTeam": game[7] if len(game) > 7 else None,
                    "homeScore": game[8] if len(game) > 8 else None,
                    "awayScore": game[9] if len(game) > 9 else None
                })
            
            return games_data
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []
    
    def get_box_score(self, game_id: str) -> List[Dict]:
        """Fetch box score for a specific game.
        
        Args:
            game_id: NBA game ID
        
        Returns:
            List of box score dictionaries
        """
        self._rate_limit()
        
        try:
            box_score = BoxScoreTraditionalV2(game_id=game_id)
            df = box_score.get_data_frames()[0]  # Player stats
            
            box_scores_data = []
            for _, row in df.iterrows():
                box_scores_data.append({
                    "playerName": row.get("PLAYER_NAME", ""),
                    "minutes": row.get("MIN", ""),
                    "points": int(row.get("PTS", 0)) if pd.notna(row.get("PTS")) else 0,
                    "rebounds": int(row.get("REB", 0)) if pd.notna(row.get("REB")) else 0,
                    "assists": int(row.get("AST", 0)) if pd.notna(row.get("AST")) else 0,
                    "steals": int(row.get("STL", 0)) if pd.notna(row.get("STL")) else 0,
                    "blocks": int(row.get("BLK", 0)) if pd.notna(row.get("BLK")) else 0,
                    "turnovers": int(row.get("TOV", 0)) if pd.notna(row.get("TOV")) else 0,
                    "personalFouls": int(row.get("PF", 0)) if pd.notna(row.get("PF")) else 0,
                    "fieldGoalsMade": int(row.get("FGM", 0)) if pd.notna(row.get("FGM")) else 0,
                    "fieldGoalsAttempted": int(row.get("FGA", 0)) if pd.notna(row.get("FGA")) else 0,
                    "threePointersMade": int(row.get("FG3M", 0)) if pd.notna(row.get("FG3M")) else 0,
                    "threePointersAttempted": int(row.get("FG3A", 0)) if pd.notna(row.get("FG3A")) else 0,
                    "freeThrowsMade": int(row.get("FTM", 0)) if pd.notna(row.get("FTM")) else 0,
                    "freeThrowsAttempted": int(row.get("FTA", 0)) if pd.notna(row.get("FTA")) else 0,
                    "plusMinus": int(row.get("PLUS_MINUS", 0)) if pd.notna(row.get("PLUS_MINUS")) else 0
                })
            
            return box_scores_data
        except Exception as e:
            print(f"Error fetching box score for game {game_id}: {e}")
            return []

