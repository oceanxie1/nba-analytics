"""Test script to see what a single box score API call returns."""
import sys
from app.db import SessionLocal
from app.ingestion.nba_api_client import NBAAPIClient
from app.models import Player

def test_box_score(game_id: str):
    """Test fetching a single box score and show what it returns."""
    print(f"🧪 Testing box score for game: {game_id}")
    print("=" * 60)
    
    # Initialize client
    client = NBAAPIClient()
    
    # Fetch box score
    print(f"\n📡 Fetching box score from API...")
    box_scores_data = client.get_box_score(game_id)
    
    print(f"\n📊 Results:")
    print(f"   Number of entries returned: {len(box_scores_data)}")
    
    if not box_scores_data:
        print("   ❌ No box score data returned!")
        return
    
    # Show first few entries
    print(f"\n📝 First 5 box score entries:")
    for i, entry in enumerate(box_scores_data[:5], 1):
        print(f"\n   Entry {i}:")
        for key, value in entry.items():
            print(f"      {key}: {value}")
    
    # Check player names against database
    print(f"\n🔍 Checking player names against database...")
    db = SessionLocal()
    try:
        # Get all players from database
        players = db.query(Player).all()
        player_map = {player.name: player.id for player in players}
        
        print(f"   Database has {len(player_map)} players")
        print(f"   Sample player names from DB: {list(player_map.keys())[:5]}")
        
        # Check if box score player names match
        print(f"\n   Player name matching:")
        matched = 0
        not_matched = []
        
        for entry in box_scores_data[:10]:  # Check first 10
            player_name = entry.get("playerName") or entry.get("name", "")
            if player_name:
                if player_name in player_map:
                    matched += 1
                    print(f"      ✅ '{player_name}' → Found (ID: {player_map[player_name]})")
                else:
                    not_matched.append(player_name)
                    print(f"      ❌ '{player_name}' → NOT FOUND")
        
        print(f"\n   Summary:")
        print(f"      Matched: {matched}/{min(10, len(box_scores_data))}")
        print(f"      Not matched: {len(not_matched)}")
        if not_matched:
            print(f"      Unmatched names: {not_matched[:5]}")
            
    finally:
        db.close()

if __name__ == "__main__":
    # Default to a game ID from the season, or use command line arg
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
    else:
        # Use a game ID from 2023-24 season (first game)
        game_id = "0022300001"
        print(f"ℹ️  No game ID provided, using default: {game_id}")
        print(f"   Usage: python test_single_boxscore.py <game_id>")
        print()
    
    test_box_score(game_id)

