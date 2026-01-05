"""Test script for player comparison endpoint."""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_response(title, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(response.text)
    print()

def test_comparison():
    """Test player comparison endpoint."""
    print("🚀 Testing Player Comparison API\n")
    
    # First, get some players to compare
    print("1️⃣ Getting list of players...")
    response = requests.get(f"{BASE_URL}/players/?limit=5")
    print_response("GET /players/?limit=5", response)
    
    if response.status_code == 200:
        players = response.json()
        if len(players) >= 2:
            player_ids = [p["id"] for p in players[:3]]  # Get first 3 players
            player_names = [p["name"] for p in players[:3]]
            
            print(f"\n2️⃣ Comparing players: {', '.join(player_names)}")
            print(f"   Player IDs: {player_ids}")
            
            # Test comparison
            player_ids_str = ",".join(map(str, player_ids))
            response = requests.get(
                f"{BASE_URL}/players/compare",
                params={
                    "player_ids": player_ids_str,
                    "season": "2023-24"
                }
            )
            print_response(
                f"GET /players/compare?player_ids={player_ids_str}&season=2023-24",
                response
            )
        else:
            print("\n⚠️  Not enough players in database to test comparison")
            print("   Need at least 2 players with stats for season 2023-24")
    else:
        print("\n❌ Could not fetch players. Is the server running?")
        print(f"   Try: uvicorn app.main:app --reload")

if __name__ == "__main__":
    try:
        test_comparison()
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error: Is the server running?")
        print("   Start the server with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

