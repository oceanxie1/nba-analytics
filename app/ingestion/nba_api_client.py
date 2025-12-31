"""NBA API client using the nba_api Python library (recommended)."""
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from nba_api.stats.endpoints import (
    commonallplayers,
    commonteamyears,
    ScoreboardV2,
    BoxScoreTraditionalV2,
    playergamelog,
    commonteamroster
)
from nba_api.stats.static import teams, players
import time


class NBAAPIClient:
    """Client using the nba_api library (more reliable than direct API calls)."""
    
    def __init__(self, rate_limit_delay: float = 2.0):
        """Initialize NBA API client.
        
        Args:
            rate_limit_delay: Seconds to wait between API calls (default: 2.0s to avoid throttling)
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self._team_id_to_abbr = {}  # Cache for team ID to abbreviation mapping
        self._request_count = 0  # Track number of requests
        self._slow_request_count = 0  # Track slow requests
        self._consecutive_failures = 0  # Track consecutive failures
        self._circuit_breaker_active = False  # Circuit breaker to pause after many failures
    
    def _rate_limit(self):
        """Enforce rate limiting with adaptive delay and circuit breaker."""
        # Circuit breaker: if we've had too many failures, pause longer
        if self._circuit_breaker_active:
            pause_time = 30.0  # 30 second pause
            print(f"   🔴 Circuit breaker active. Pausing {pause_time}s to let API recover...")
            time.sleep(pause_time)
            self._circuit_breaker_active = False
            self._consecutive_failures = 0  # Reset after pause
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Increase delay after many requests or slow requests (API might throttle)
        self._request_count += 1
        adaptive_delay = self.rate_limit_delay
        
        # Aggressively increase delay if we've had consecutive failures (API is throttling)
        if self._consecutive_failures >= 10:
            # Activate circuit breaker after 10 consecutive failures
            self._circuit_breaker_active = True
            adaptive_delay = 10.0  # Very long delay
        elif self._consecutive_failures > 5:
            adaptive_delay = self.rate_limit_delay * 8.0  # 8x delay after many failures
            print(f"   ⚠️  Heavy API throttling detected. Increasing delay to {adaptive_delay:.1f}s...")
        elif self._consecutive_failures > 2:
            adaptive_delay = self.rate_limit_delay * 4.0  # 4x delay after some failures
        elif self._slow_request_count > 5:
            adaptive_delay = self.rate_limit_delay * 2.0  # Double the delay
        elif self._slow_request_count > 2:
            adaptive_delay = self.rate_limit_delay * 1.5
        elif self._request_count > 100:
            # After 100 requests, start increasing delay gradually (sooner than before)
            multiplier = 1.0 + (self._request_count - 100) / 300  # Gradually increase
            adaptive_delay = self.rate_limit_delay * multiplier
        
        if time_since_last < adaptive_delay:
            time.sleep(adaptive_delay - time_since_last)
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
            # Method 1: Try to get players from team rosters (more complete)
            # This gets all players currently on team rosters
            print(f"   📡 Fetching players from team rosters...")
            players_data = []
            seen_player_ids = set()  # Track by ID to avoid duplicates
            
            # Get all teams first
            nba_teams = teams.get_teams()
            team_count = 0
            
            for team in nba_teams:
                team_id = team["id"]
                self._rate_limit()  # Rate limit between team requests
                
                try:
                    roster = commonteamroster.CommonTeamRoster(
                        season=season,
                        team_id=team_id
                    )
                    df_roster = roster.get_data_frames()[0]
                    
                    if not df_roster.empty:
                        team_count += 1
                        for _, row in df_roster.iterrows():
                            player_id = row.get("PLAYER_ID")
                            if player_id and player_id not in seen_player_ids:
                                seen_player_ids.add(player_id)
                                player_name = row.get("PLAYER", "")
                                if player_name and not pd.isna(player_name):
                                    players_data.append({
                                        "name": player_name,
                                        "playerId": player_id,
                                        "teamAbbreviation": team["abbreviation"],
                                        "position": row.get("POSITION", None),
                                        "height": row.get("HEIGHT", None),
                                        "weight": row.get("WEIGHT", None)
                                    })
                except Exception as e:
                    # Skip teams that fail, continue with others
                    continue
            
            print(f"   📊 Found {len(players_data)} players from {team_count} team rosters")
            
            # Method 2: Fallback - if we got very few players, try CommonAllPlayers
            if len(players_data) < 200:
                print(f"   ⚠️  Got fewer players than expected, trying CommonAllPlayers as fallback...")
                self._rate_limit()
                all_players = commonallplayers.CommonAllPlayers(
                    is_only_current_season=1,
                    league_id='00',
                    season=season
                )
                df = all_players.get_data_frames()[0]
                
                if not df.empty:
                    # Add players we haven't seen yet
                    for _, row in df.iterrows():
                        player_id = row.get("PERSON_ID")
                        if player_id and player_id not in seen_player_ids:
                            seen_player_ids.add(player_id)
                            player_name = row.get("DISPLAY_FIRST_LAST", "")
                            if player_name and not pd.isna(player_name):
                                players_data.append({
                                    "name": player_name,
                                    "playerId": player_id,
                                    "teamAbbreviation": row.get("TEAM_ABBREVIATION", ""),
                                    "position": None,
                                    "height": None,
                                    "weight": None
                                })
                    print(f"   📊 Added {len(players_data)} total players (including fallback)")
            
            if not players_data:
                print(f"⚠️  No players found")
                return []
            
            print(f"   ✅ Processed {len(players_data)} unique players")
            return players_data
        except KeyError as e:
            print(f"Error fetching players (KeyError): {e}")
            print(f"   This usually means the API response format changed or season '{season}' is invalid")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"Error fetching players: {e}")
            import traceback
            traceback.print_exc()
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
    
    def get_box_score(self, game_id: str, max_retries: int = 3, timeout: int = 10) -> List[Dict]:
        """Fetch box score for a specific game with retry logic.
        
        Args:
            game_id: NBA game ID (should be 10 digits, e.g., "0022300270")
            max_retries: Maximum number of retry attempts
            timeout: Timeout in seconds (not directly used by nba_api, but tracked)
        
        Returns:
            List of box score dictionaries (empty list on failure or invalid game)
        """
        import time as time_module
        
        # Validate game ID format
        if not game_id or len(str(game_id)) != 10:
            print(f"   ⚠️  Invalid game ID format: {game_id} (expected 10 digits)")
            return []
        
        for attempt in range(max_retries):
            self._rate_limit()
            
            try:
                start_time = time_module.time()
                box_score = BoxScoreTraditionalV2(game_id=game_id)
                df = box_score.get_data_frames()[0]  # Player stats
                elapsed = time_module.time() - start_time
                
                # Check if this is a valid response or an error
                # Sometimes the API returns empty data for games that don't exist
                if df.empty:
                    # This could mean the game doesn't have box scores yet (future game, cancelled, etc.)
                    if attempt == 0:  # Only log on first attempt
                        print(f"   ℹ️  No box score data available for game {game_id} (may be future/cancelled game)")
                    return []
                
                # Track slow requests
                if elapsed > 5.0:
                    self._slow_request_count += 1
                    if attempt == 0:  # Only log on first attempt
                        print(f"   ⚠️  Slow box score API call: {elapsed:.1f}s for game {game_id}")
                else:
                    # Reset slow count if we get a fast request
                    if self._slow_request_count > 0:
                        self._slow_request_count = max(0, self._slow_request_count - 1)
                
                if df.empty:
                    return []
                
                # Use itertuples() instead of iterrows() - MUCH faster (10-100x)
                # itertuples() is significantly faster because it returns named tuples
                box_scores_data = []
                for row in df.itertuples(index=False):
                    # Skip players with no stats (DNP, etc.)
                    min_value = getattr(row, 'MIN', None)
                    if min_value is None or min_value == "" or (isinstance(min_value, float) and pd.isna(min_value)):
                        continue
                    
                    # Clean up minutes value - handle edge cases
                    minutes_str = str(min_value).strip()
                    if not minutes_str or minutes_str == "nan":
                        continue
                    
                    # Use getattr for faster access (itertuples uses named tuples)
                    # Handle NaN values properly
                    def safe_int(val, default=0):
                        if val is None or (isinstance(val, float) and pd.isna(val)):
                            return default
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            return default
                    
                    box_scores_data.append({
                        "playerName": getattr(row, 'PLAYER_NAME', ''),
                        "minutes": minutes_str,
                        "points": safe_int(getattr(row, 'PTS', None), 0),
                        "rebounds": safe_int(getattr(row, 'REB', None), 0),
                        "assists": safe_int(getattr(row, 'AST', None), 0),
                        "steals": safe_int(getattr(row, 'STL', None), 0),
                        "blocks": safe_int(getattr(row, 'BLK', None), 0),
                        "turnovers": safe_int(getattr(row, 'TOV', None), 0),
                        "personalFouls": safe_int(getattr(row, 'PF', None), 0),
                        "fieldGoalsMade": safe_int(getattr(row, 'FGM', None), 0),
                        "fieldGoalsAttempted": safe_int(getattr(row, 'FGA', None), 0),
                        "threePointersMade": safe_int(getattr(row, 'FG3M', None), 0),
                        "threePointersAttempted": safe_int(getattr(row, 'FG3A', None), 0),
                        "freeThrowsMade": safe_int(getattr(row, 'FTM', None), 0),
                        "freeThrowsAttempted": safe_int(getattr(row, 'FTA', None), 0),
                        "plusMinus": safe_int(getattr(row, 'PLUS_MINUS', None), 0)
                    })
                
                return box_scores_data
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if this is a "game not found" type error vs a timeout
                if "404" in error_str or "not found" in error_str or "invalid" in error_str:
                    # Game doesn't exist or is invalid - don't retry, just skip
                    print(f"   ⚠️  Game {game_id} not found or invalid - skipping")
                    return []
                
                # Track consecutive failures (only for real errors, not "not found")
                self._consecutive_failures += 1
                
                if attempt < max_retries - 1:
                    # Exponential backoff with much longer waits for timeouts
                    if "timeout" in error_str or "timed out" in error_str:
                        wait_time = (2 ** attempt) * 5  # Much longer wait for timeouts: 5s, 10s, 20s
                    else:
                        wait_time = (2 ** attempt) * 2  # Longer normal backoff: 2s, 4s, 8s
                    
                    print(f"   ⚠️  Error fetching box score for game {game_id} (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    print(f"   ❌ Failed to fetch box score for game {game_id} after {max_retries} attempts: {e}")
                    # Add extra delay after failure to avoid hammering the API
                    if self._consecutive_failures > 3:
                        extra_delay = 10.0  # Longer pause
                        print(f"   ⏸️  Pausing {extra_delay}s to avoid API throttling...")
                        time.sleep(extra_delay)
                    return []
        
        return []  # Should never reach here, but just in case

