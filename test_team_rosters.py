"""Test fetching players from team rosters."""
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import teams
import pandas as pd

def test_team_rosters(season: str = "2023-24"):
    """Test fetching players from each team's roster."""
    print(f"🧪 Testing Team Rosters for season: {season}")
    print("=" * 60)
    
    nba_teams = teams.get_teams()
    all_players = []
    seen_player_ids = set()
    
    print(f"\n📊 Fetching rosters from {len(nba_teams)} teams...")
    
    for i, team in enumerate(nba_teams, 1):
        team_id = team["id"]
        team_abbr = team["abbreviation"]
        
        try:
            roster = commonteamroster.CommonTeamRoster(
                season=season,
                team_id=team_id
            )
            df_roster = roster.get_data_frames()[0]
            
            if not df_roster.empty:
                team_players = []
                for _, row in df_roster.iterrows():
                    player_id = row.get("PLAYER_ID")
                    if player_id and player_id not in seen_player_ids:
                        seen_player_ids.add(player_id)
                        player_name = row.get("PLAYER", "")
                        if player_name:
                            team_players.append(player_name)
                            all_players.append({
                                "name": player_name,
                                "team": team_abbr,
                                "position": row.get("POSITION", ""),
                                "height": row.get("HEIGHT", ""),
                                "weight": row.get("WEIGHT", "")
                            })
                
                print(f"   {team_abbr}: {len(team_players)} players")
                if team_players:
                    print(f"      Sample: {team_players[:3]}")
            else:
                print(f"   {team_abbr}: No roster data")
                
        except Exception as e:
            print(f"   {team_abbr}: Error - {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Total unique players: {len(all_players)}")
    print(f"   Teams processed: {len([t for t in nba_teams])}")
    
    # Show sample players
    print(f"\n📝 Sample players:")
    for player in all_players[:10]:
        print(f"   - {player['name']} ({player['team']}) - {player['position']}")

if __name__ == "__main__":
    import sys
    season = sys.argv[1] if len(sys.argv) > 1 else "2023-24"
    test_team_rosters(season)



