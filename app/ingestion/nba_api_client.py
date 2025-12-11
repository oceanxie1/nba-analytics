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
        self._team_id_to_abbr = {}  # Cache for team ID to abbreviation mapping
    
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
            
            # Also create a mapping of team ID to abbreviation for games
            self._team_id_to_abbr = {team["id"]: team["abbreviation"] for team in nba_teams}
            
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
                      If "season", fetches all games for the season.
        
        Returns:
            List of game dictionaries
        """
        if game_date == "season":
            # Fetch all games for the season
            return self.get_games_for_season(season)
        
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
            result_sets = games_dict.get("resultSets", [])
            if result_sets and len(result_sets) > 1:
                games_info = result_sets[0].get("rowSet", [])
                teams_info = result_sets[1].get("rowSet", [])
                
                # Build team scores map
                game_teams = {}
                for team_row in teams_info:
                    if len(team_row) >= 5:
                        game_id = team_row[2]
                        team_abbr = team_row[4]
                        team_id = team_row[3]
                        total_pts = sum(int(team_row[i]) for i in range(8, 15) if len(team_row) > i and team_row[i] is not None)
                        
                        if game_id not in game_teams:
                            game_teams[game_id] = {}
                        game_teams[game_id][team_abbr] = {"team_id": team_id, "points": total_pts}
                
                # Process games
                for game in games_info:
                    if len(game) >= 8:
                        game_id = str(game[2])
                        game_date_est = game[0]
                        home_team_id = game[6]
                        visitor_team_id = game[7]
                        
                        home_team_abbr = self._team_id_to_abbr.get(home_team_id)
                        away_team_abbr = self._team_id_to_abbr.get(visitor_team_id)
                        
                        home_score = None
                        away_score = None
                        if game_id in game_teams:
                            for abbr, team_data in game_teams[game_id].items():
                                if team_data["team_id"] == home_team_id:
                                    home_score = team_data["points"]
                                elif team_data["team_id"] == visitor_team_id:
                                    away_score = team_data["points"]
                        
                        if home_team_abbr and away_team_abbr:
                            games_data.append({
                                "gameId": game_id,
                                "gameDate": game_date_est.split("T")[0] if "T" in str(game_date_est) else str(game_date_est),
                                "homeTeam": home_team_abbr,
                                "awayTeam": away_team_abbr,
                                "homeScore": home_score,
                                "awayScore": away_score
                            })
            
            return games_data
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []
    
    def get_games_for_season(self, season: str) -> List[Dict]:
        """Fetch all games for an entire season by iterating through dates.
        
        Args:
            season: Season year (e.g., "2023-24")
        
        Returns:
            List of game dictionaries for the entire season
        """
        from datetime import date, timedelta
        
        # Parse season to get start and end dates
        # NBA season typically runs from October to June
        year_start = int(season.split("-")[0])
        year_end = year_start + 1
        
        # Season starts in October
        start_date = date(year_start, 10, 1)
        # Season ends in June of next year
        end_date = date(year_end, 6, 30)
        
        all_games = []
        current_date = start_date
        games_found = 0
        consecutive_empty_days = 0
        max_empty_days = 7  # Stop after 7 consecutive days with no games
        
        print(f"   Fetching games from {start_date} to {end_date}...")
        
        while current_date <= end_date:
            # Skip if we've had too many consecutive empty days (likely past season end)
            if consecutive_empty_days >= max_empty_days:
                print(f"   Stopping early: {consecutive_empty_days} consecutive days with no games")
                break
            
            self._rate_limit()
            date_str = current_date.strftime("%m/%d/%Y")
            
            try:
                scoreboard_data = ScoreboardV2(game_date=date_str)
                games_dict = scoreboard_data.get_dict()
                
                result_sets = games_dict.get("resultSets", [])
                if result_sets and len(result_sets) > 1:
                    # ResultSet 0: Game info [GAME_DATE_EST, GAME_SEQUENCE, GAME_ID, ..., HOME_TEAM_ID, VISITOR_TEAM_ID, ...]
                    games_info = result_sets[0].get("rowSet", [])
                    # ResultSet 1: Team line scores [GAME_DATE_EST, GAME_SEQUENCE, GAME_ID, TEAM_ID, TEAM_ABBREVIATION, ..., PTS_QTR1, PTS_QTR2, PTS_QTR3, PTS_QTR4, ...]
                    teams_info = result_sets[1].get("rowSet", [])
                    
                    if games_info:
                        consecutive_empty_days = 0
                        
                        # Create a map of game_id -> {home_team: {...}, away_team: {...}}
                        game_teams = {}
                        for team_row in teams_info:
                            if len(team_row) >= 5:
                                game_id = team_row[2]  # GAME_ID
                                team_abbr = team_row[4]  # TEAM_ABBREVIATION
                                team_id = team_row[3]  # TEAM_ID
                                
                                # Calculate total points from quarters (indices 8-11: PTS_QTR1-4, 12-14: OT)
                                total_pts = 0
                                for i in range(8, 15):  # Quarters 1-4 + up to 3 OTs
                                    if len(team_row) > i and team_row[i] is not None:
                                        total_pts += int(team_row[i])
                                
                                if game_id not in game_teams:
                                    game_teams[game_id] = {}
                                
                                # Determine if home or away based on team_id matching games_info
                                game_teams[game_id][team_abbr] = {
                                    "team_id": team_id,
                                    "points": total_pts
                                }
                        
                        # Process games
                        for game in games_info:
                            if len(game) >= 8:
                                game_id = str(game[2])  # GAME_ID at index 2
                                game_date_est = game[0]  # GAME_DATE_EST at index 0
                                home_team_id = game[6]  # HOME_TEAM_ID at index 6
                                visitor_team_id = game[7]  # VISITOR_TEAM_ID at index 7
                                
                                # Get team abbreviations from mapping
                                home_team_abbr = self._team_id_to_abbr.get(home_team_id)
                                away_team_abbr = self._team_id_to_abbr.get(visitor_team_id)
                                
                                # Get scores from game_teams map
                                home_score = None
                                away_score = None
                                if game_id in game_teams:
                                    for abbr, team_data in game_teams[game_id].items():
                                        if team_data["team_id"] == home_team_id:
                                            home_score = team_data["points"]
                                        elif team_data["team_id"] == visitor_team_id:
                                            away_score = team_data["points"]
                                
                                if home_team_abbr and away_team_abbr:
                                    all_games.append({
                                        "gameId": game_id,
                                        "gameDate": game_date_est.split("T")[0] if "T" in str(game_date_est) else str(game_date_est),
                                        "homeTeam": home_team_abbr,
                                        "awayTeam": away_team_abbr,
                                        "homeScore": home_score,
                                        "awayScore": away_score
                                    })
                                    games_found += 1
                    else:
                        consecutive_empty_days += 1
                else:
                    consecutive_empty_days += 1
                    
            except Exception as e:
                # Skip errors for individual dates
                consecutive_empty_days += 1
                pass
            
            # Move to next day
            current_date += timedelta(days=1)
            
            # Progress update every 30 days
            if (current_date - start_date).days % 30 == 0:
                print(f"   Progress: {current_date.strftime('%Y-%m-%d')} - Found {games_found} games so far...")
        
        print(f"   ✅ Found {len(all_games)} total games for season {season}")
        return all_games
    
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
            
            if df.empty:
                return []
            
            box_scores_data = []
            for _, row in df.iterrows():
                # Skip players with no stats (DNP, etc.)
                min_value = row.get("MIN")
                if pd.isna(min_value) or min_value == "" or min_value is None:
                    continue
                
                # Clean up minutes value - handle edge cases
                minutes_str = str(min_value).strip()
                if not minutes_str or minutes_str == "nan":
                    continue
                    
                box_scores_data.append({
                    "playerName": row.get("PLAYER_NAME", ""),
                    "minutes": minutes_str,
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
            # Silently skip errors (game might not have box score data yet)
            return []

