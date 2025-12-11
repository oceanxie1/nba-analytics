"""Simple script to test the NBA Analytics API endpoints."""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
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

def test_api():
    """Test all API endpoints."""
    print("🚀 Testing NBA Analytics API\n")
    
    # 1. Health check
    print("1️⃣ Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print_response("GET /health", response)
    
    # 2. List teams
    print("2️⃣ Testing list teams...")
    response = requests.get(f"{BASE_URL}/teams/")
    print_response("GET /teams/", response)
    
    # 3. Get specific team
    print("3️⃣ Testing get team by ID...")
    response = requests.get(f"{BASE_URL}/teams/1")
    print_response("GET /teams/1", response)
    
    # 4. List players
    print("4️⃣ Testing list players...")
    response = requests.get(f"{BASE_URL}/players/")
    print_response("GET /players/", response)
    
    # 5. Get specific player
    print("5️⃣ Testing get player by ID...")
    response = requests.get(f"{BASE_URL}/players/1")
    print_response("GET /players/1", response)
    
    # 6. Get player season stats
    print("6️⃣ Testing player season stats...")
    response = requests.get(f"{BASE_URL}/players/1/stats/2023-24")
    print_response("GET /players/1/stats/2023-24", response)
    
    # 7. List games
    print("7️⃣ Testing list games...")
    response = requests.get(f"{BASE_URL}/games/")
    print_response("GET /games/", response)
    
    # 8. Create a new team (POST)
    print("8️⃣ Testing create team...")
    new_team = {
        "name": "Miami Heat",
        "abbreviation": "MIA",
        "city": "Miami",
        "conference": "East",
        "division": "Southeast"
    }
    response = requests.post(f"{BASE_URL}/teams/", json=new_team)
    print_response("POST /teams/", response)
    
    # 9. Filter players by team
    print("9️⃣ Testing filter players by team...")
    response = requests.get(f"{BASE_URL}/players/?team_id=1")
    print_response("GET /players/?team_id=1", response)
    
    print("\n✅ Testing complete!")
    print(f"\n💡 Tip: Visit {BASE_URL}/docs for interactive API testing")
    print(f"💡 Tip: Visit {BASE_URL}/redoc for alternative docs")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API.")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

