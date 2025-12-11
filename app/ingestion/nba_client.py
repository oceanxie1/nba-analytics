"""NBA API client for fetching data."""
import requests
import time
from typing import List, Dict, Optional
from datetime import date, datetime


class NBAClient:
    """Client for fetching NBA data from stats.nba.com API."""
    
    BASE_URL = "https://stats.nba.com/stats"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nba.com/",
    }
    
    def __init__(self, rate_limit_delay: float = 0.6):
        """Initialize NBA API client.
        
        Args:
            rate_limit_delay: Seconds to wait between API calls to avoid rate limiting
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request with rate limiting."""
        self._rate_limit()
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, headers=self.HEADERS, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"⚠️  Timeout connecting to NBA API endpoint: {endpoint}")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"⚠️  HTTP error from NBA API: {e.response.status_code} for {endpoint}")
            raise
        except Exception as e:
            print(f"⚠️  Error connecting to NBA API: {e}")
            raise
    
    def get_teams(self, season: Optional[str] = None) -> List[Dict]:
        """Fetch all NBA teams.
        
        Args:
            season: Season year (e.g., "2023-24"). If None, uses current season.
        
        Returns:
            List of team dictionaries with team info
        """
        if not season:
            # Default to current season
            current_year = datetime.now().year
            if datetime.now().month >= 10:  # NBA season starts in October
                season = f"{current_year}-{str(current_year + 1)[2:]}"
            else:
                season = f"{current_year - 1}-{str(current_year)[2:]}"
        
        params = {
            "LeagueID": "00",
            "Season": season,
            "IsOnlyCurrentSeason": "1"
        }
        
        try:
            data = self._make_request("commonTeamYears", params)
            # Note: This endpoint structure may vary. Adjust based on actual API response.
            # For now, return a simplified structure
            return data.get("resultSets", [{}])[0].get("rowSet", [])
        except Exception as e:
            print(f"Error fetching teams: {e}")
            # Return empty list on error
            return []
    
    def get_players(self, season: Optional[str] = None, team_id: Optional[int] = None) -> List[Dict]:
        """Fetch players.
        
        Args:
            season: Season year (e.g., "2023-24")
            team_id: Optional team ID to filter players
        
        Returns:
            List of player dictionaries
        """
        if not season:
            current_year = datetime.now().year
            if datetime.now().month >= 10:
                season = f"{current_year}-{str(current_year + 1)[2:]}"
            else:
                season = f"{current_year - 1}-{str(current_year)[2:]}"
        
        params = {
            "LeagueID": "00",
            "Season": season,
            "IsOnlyCurrentSeason": "1"
        }
        
        if team_id:
            params["TeamID"] = team_id
        
        try:
            data = self._make_request("commonallplayers", params)
            return data.get("resultSets", [{}])[0].get("rowSet", [])
        except Exception as e:
            print(f"Error fetching players: {e}")
            return []
    
    def get_games(self, season: str, start_date: Optional[str] = None, 
                  end_date: Optional[str] = None) -> List[Dict]:
        """Fetch games for a season or date range.
        
        Args:
            season: Season year (e.g., "2023-24")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of game dictionaries
        """
        params = {
            "LeagueID": "00",
            "Season": season,
            "SeasonType": "Regular Season"
        }
        
        if start_date:
            params["DateFrom"] = start_date
        if end_date:
            params["DateTo"] = end_date
        
        try:
            data = self._make_request("scoreboard", params)
            return data.get("resultSets", [{}])[0].get("rowSet", [])
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []
    
    def get_box_score(self, game_id: str) -> List[Dict]:
        """Fetch box score for a specific game.
        
        Args:
            game_id: NBA game ID
        
        Returns:
            List of box score dictionaries (one per player)
        """
        params = {
            "GameID": game_id,
            "EndPeriod": "10",
            "EndRange": "28800",
            "RangeType": "0",
            "StartPeriod": "1",
            "StartRange": "0"
        }
        
        try:
            data = self._make_request("boxscoretraditionalv2", params)
            return data.get("resultSets", [{}])[0].get("rowSet", [])
        except Exception as e:
            print(f"Error fetching box score for game {game_id}: {e}")
            return []

