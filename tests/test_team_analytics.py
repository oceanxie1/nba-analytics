"""Test script for team analytics endpoints."""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"


def print_response(title, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text)
    else:
        print(response.text)
    print()


def test_team_analytics():
    """Test all team analytics endpoints."""
    print("🚀 Testing Team Analytics API\n")
    
    # 1. Get a team first
    print("1️⃣ Getting a team...")
    response = requests.get(f"{BASE_URL}/teams/")
    if response.status_code == 200:
        teams = response.json()
        if teams:
            team_id = teams[0]["id"]
            team_name = teams[0]["name"]
            print(f"   Using team: {team_name} (ID: {team_id})")
        else:
            print("   ⚠️  No teams found. Please ingest data first.")
            return
    else:
        print(f"   ❌ Failed to get teams: {response.status_code}")
        return
    
    # 2. Get team season stats
    print("\n2️⃣ Testing team season stats...")
    season = "2023-24"  # Adjust based on your data
    response = requests.get(f"{BASE_URL}/teams/{team_id}/stats/{season}")
    print_response(f"GET /teams/{team_id}/stats/{season}", response)
    
    # 3. Get team games
    print("\n3️⃣ Testing team games...")
    response = requests.get(f"{BASE_URL}/teams/{team_id}/games?season={season}")
    print_response(f"GET /teams/{team_id}/games?season={season}", response)
    
    # 4. Get a game ID for testing
    if response.status_code == 200:
        games = response.json()
        if games:
            game_id = games[0]["id"]
            print(f"\n4️⃣ Testing game team stats with game {game_id}...")
            
            # Get team stats for this game
            response = requests.get(f"{BASE_URL}/teams/{team_id}/games/{game_id}/stats")
            print_response(f"GET /teams/{team_id}/games/{game_id}/stats", response)
            
            # Get game team stats (both teams)
            print("\n5️⃣ Testing game team stats (both teams)...")
            response = requests.get(f"{BASE_URL}/games/{game_id}/team-stats")
            print_response(f"GET /games/{game_id}/team-stats", response)
            
            # Get game summary
            print("\n6️⃣ Testing game summary...")
            response = requests.get(f"{BASE_URL}/games/{game_id}/summary")
            print_response(f"GET /games/{game_id}/summary", response)
        else:
            print("   ⚠️  No games found for this team.")
    else:
        print("   ⚠️  Could not get games to test game endpoints.")
    
    print("\n✅ Team analytics testing complete!")
    print(f"\n💡 Tip: Visit {BASE_URL}/docs for interactive API testing")


if __name__ == "__main__":
    try:
        test_team_analytics()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

