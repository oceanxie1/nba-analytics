"""Test script to see what the players API actually returns."""
import sys
from nba_api.stats.endpoints import commonallplayers
import pandas as pd

def test_players_api(season: str = "2023-24"):
    """Test different ways of fetching players."""
    print(f"🧪 Testing Players API for season: {season}")
    print("=" * 60)
    
    # Test 1: Current season only
    print("\n📊 Test 1: Current season only (is_only_current_season=1)")
    try:
        all_players = commonallplayers.CommonAllPlayers(
            is_only_current_season=1,
            league_id='00',
            season=season
        )
        df1 = all_players.get_data_frames()[0]
        print(f"   ✅ Found {len(df1)} players")
        if not df1.empty:
            print(f"   Sample columns: {list(df1.columns)[:5]}")
            print(f"   Sample players:")
            for i, row in df1.head(5).iterrows():
                name = row.get("DISPLAY_FIRST_LAST", "N/A")
                team = row.get("TEAM_ABBREVIATION", "N/A")
                print(f"      - {name} ({team})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: All players (not just current season)
    print("\n📊 Test 2: All players (is_only_current_season=0)")
    try:
        all_players = commonallplayers.CommonAllPlayers(
            is_only_current_season=0,
            league_id='00'
        )
        df2 = all_players.get_data_frames()[0]
        print(f"   ✅ Found {len(df2)} players")
        if not df2.empty:
            print(f"   Sample players:")
            for i, row in df2.head(5).iterrows():
                name = row.get("DISPLAY_FIRST_LAST", "N/A")
                team = row.get("TEAM_ABBREVIATION", "N/A")
                print(f"      - {name} ({team})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check team distribution
    print("\n📊 Test 3: Team distribution (current season)")
    try:
        all_players = commonallplayers.CommonAllPlayers(
            is_only_current_season=1,
            league_id='00',
            season=season
        )
        df3 = all_players.get_data_frames()[0]
        if not df3.empty:
            # Count players per team
            team_counts = df3.groupby("TEAM_ABBREVIATION").size()
            print(f"   Teams with players: {len(team_counts)}")
            print(f"   Players per team:")
            for team, count in team_counts.items():
                print(f"      {team}: {count} players")
            print(f"   Total: {team_counts.sum()} players")
            
            # Check for players without teams
            no_team = df3[df3["TEAM_ABBREVIATION"].isna() | (df3["TEAM_ABBREVIATION"] == "")]
            if len(no_team) > 0:
                print(f"\n   ⚠️  Found {len(no_team)} players without teams:")
                for i, row in no_team.head(5).iterrows():
                    name = row.get("DISPLAY_FIRST_LAST", "N/A")
                    print(f"      - {name}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Check what columns are available
    print("\n📊 Test 4: Available columns")
    try:
        all_players = commonallplayers.CommonAllPlayers(
            is_only_current_season=1,
            league_id='00',
            season=season
        )
        df4 = all_players.get_data_frames()[0]
        if not df4.empty:
            print(f"   Columns: {list(df4.columns)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    season = sys.argv[1] if len(sys.argv) > 1 else "2023-24"
    test_players_api(season)

