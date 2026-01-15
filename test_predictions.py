#!/usr/bin/env python3
"""Script to test game outcome predictions."""
import sys
import os
import random
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, init_db
from app.ml.models import load_game_outcome_model, predict_game_outcome
from app.ml.data_prep import prepare_features_for_prediction
from app.models import Team, Game


def test_direct():
    """Test predictions directly (no API server)."""
    print("🏀 Testing Game Outcome Predictions (Direct)")
    print("=" * 50)
    
    init_db()
    db = SessionLocal()
    
    try:
        # Load model
        model = load_game_outcome_model()
        if not model:
            print("\n❌ No trained model found. Please run train_model.py first.")
            return
        
        # Try to find actual upcoming games (games without scores)
        today = date.today()
        upcoming_games = db.query(Game).filter(
            Game.game_date >= today,
            Game.home_score.is_(None)
        ).order_by(Game.game_date).limit(5).all()
        
        if upcoming_games:
            print(f"\n📊 Found {len(upcoming_games)} upcoming games in database")
            print("   Using actual scheduled games for predictions\n")
            
            for game in upcoming_games[:3]:  # Test up to 3 games
                home_team = game.home_team
                away_team = game.away_team
                
                if not home_team or not away_team:
                    continue
                
                print(f"{'─' * 50}")
                print(f"Game ID: {game.id}")
                print(f"Matchup: {away_team.name} @ {home_team.name}")
                print(f"Date: {game.game_date}")
                print(f"Season: {game.season}")
                
                try:
                    features_df = prepare_features_for_prediction(
                        db, game.home_team_id, game.away_team_id, game.game_date, game.season
                    )
                    
                    result = predict_game_outcome(model, features_df)
                    
                    print(f"\n✅ Prediction:")
                    print(f"   Winner: {result['predicted_winner'].upper()} ({home_team.name if result['prediction'] == 1 else away_team.name})")
                    print(f"   Confidence: {result['probability']:.1%}")
                    print(f"   Home Win Prob: {result['home_win_prob']:.1%}")
                    print(f"   Away Win Prob: {result['away_win_prob']:.1%}")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            # Fallback: use random completed games to test the model
            print("\n⚠️  No upcoming games found in database")
            print("   Using random completed games to test predictions\n")
            
            all_completed_games = db.query(Game).filter(
                Game.home_score.isnot(None),
                Game.away_score.isnot(None)
            ).all()
            
            if not all_completed_games:
                print("❌ No games found in database at all.")
                return
            
            # Randomly select up to 3 games
            selected_games = random.sample(all_completed_games, min(3, len(all_completed_games)))
            
            for game in selected_games:
                home_team = game.home_team
                away_team = game.away_team
                
                if not home_team or not away_team:
                    continue
                
                actual_winner = "HOME" if game.home_score > game.away_score else "AWAY"
                
                print(f"{'─' * 50}")
                print(f"Game ID: {game.id} (COMPLETED - for testing)")
                print(f"Matchup: {away_team.name} @ {home_team.name}")
                print(f"Date: {game.game_date}")
                print(f"Actual Result: {actual_winner} ({game.home_score}-{game.away_score})")
                
                try:
                    features_df = prepare_features_for_prediction(
                        db, game.home_team_id, game.away_team_id, game.game_date, game.season
                    )
                    
                    result = predict_game_outcome(model, features_df)
                    
                    correct = (result['prediction'] == 1 and game.home_score > game.away_score) or \
                             (result['prediction'] == 0 and game.away_score > game.home_score)
                    
                    print(f"\n✅ Prediction:")
                    print(f"   Predicted: {result['predicted_winner'].upper()} ({home_team.name if result['prediction'] == 1 else away_team.name})")
                    print(f"   Confidence: {result['probability']:.1%}")
                    print(f"   {'✓ CORRECT' if correct else '✗ INCORRECT'}")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
        
    finally:
        db.close()


def test_via_api():
    """Test predictions via API (requires server running)."""
    import requests
    
    print("🏀 Testing Game Outcome Predictions (Via API)")
    print("=" * 50)
    
    api_url = "http://localhost:8000"
    
    # Check if server is running
    print("\n🔍 Checking if API server is running...")
    try:
        response = requests.get(f"{api_url}/docs", timeout=3)
        if response.status_code != 200:
            print(f"\n❌ API server returned status {response.status_code}")
            print("   Start it with: uvicorn app.main:app --reload")
            return
        print("   ✓ Server is running")
    except requests.exceptions.ConnectionError:
        print("\n❌ API server not running.")
        print("   Start it with: uvicorn app.main:app --reload")
        return
    except requests.exceptions.Timeout:
        print("\n❌ API server connection timed out.")
        print("   Start it with: uvicorn app.main:app --reload")
        return
    except Exception as e:
        print(f"\n❌ Error connecting to API server: {e}")
        print("   Start it with: uvicorn app.main:app --reload")
        return
    
    # Get teams
    print("\n📊 Fetching teams...")
    try:
        teams_response = requests.get(f"{api_url}/teams?limit=5", timeout=5)
        teams_response.raise_for_status()
        teams = teams_response.json()
        
        # Handle both list response and paginated response
        if isinstance(teams, dict) and "items" in teams:
            teams = teams["items"]
        elif not isinstance(teams, list):
            print(f"\n❌ Unexpected response format: {type(teams)}")
            print(f"   Response: {teams}")
            return
        
        if len(teams) < 2:
            print("\n❌ Need at least 2 teams.")
            return
        
        print(f"   ✓ Found {len(teams)} teams")
        
        # Try to find actual upcoming games (games without scores)
        today = date.today()
        games_response = requests.get(
            f"{api_url}/games",
            params={"limit": 200},  # Get more games to find upcoming ones
            timeout=5
        )
        
        if games_response.status_code == 200:
            scheduled_games = games_response.json()
            if isinstance(scheduled_games, dict) and "items" in scheduled_games:
                scheduled_games = scheduled_games["items"]
            
            # Filter for upcoming games (date >= today, no scores)
            today_str = today.isoformat()
            future_games = [
                g for g in scheduled_games 
                if g.get("game_date") >= today_str and g.get("home_score") is None
            ]
            
            # Sort by date
            future_games.sort(key=lambda x: x.get("game_date", ""))
            
            if future_games:
                # Use an actual scheduled game
                game = future_games[0]
                home_team_id = game["home_team_id"]
                away_team_id = game["away_team_id"]
                game_date = game["game_date"]
                season = game["season"]
                
                # Get team names
                home_team = next((t for t in teams if t["id"] == home_team_id), None)
                away_team = next((t for t in teams if t["id"] == away_team_id), None)
                
                if not home_team or not away_team:
                    # Fetch team details if not in our list
                    home_resp = requests.get(f"{api_url}/teams/{home_team_id}", timeout=5)
                    away_resp = requests.get(f"{api_url}/teams/{away_team_id}", timeout=5)
                    if home_resp.status_code == 200:
                        home_team = home_resp.json()
                    if away_resp.status_code == 200:
                        away_team = away_resp.json()
                
                print(f"\n📊 Testing prediction for ACTUAL scheduled game:")
                print(f"   {away_team.get('name', f'Team {away_team_id}')} @ {home_team.get('name', f'Team {home_team_id}')}")
                print(f"   Date: {game_date}")
                print(f"   Season: {season}")
            else:
                # No upcoming games, try using random completed games for testing
                print(f"\n⚠️  No upcoming games found")
                print("   Using random completed game to test prediction accuracy")
                
                # Get all completed games
                completed_games = [
                    g for g in scheduled_games 
                    if g.get("home_score") is not None and g.get("away_score") is not None
                ]
                
                if completed_games:
                    # Randomly select a game
                    game = random.choice(completed_games)
                    home_team_id = game["home_team_id"]
                    away_team_id = game["away_team_id"]
                    game_date = game["game_date"]
                    season = game["season"]
                    actual_winner = "HOME" if game["home_score"] > game["away_score"] else "AWAY"
                    
                    # Get team names
                    home_team = next((t for t in teams if t["id"] == home_team_id), None)
                    away_team = next((t for t in teams if t["id"] == away_team_id), None)
                    
                    if not home_team or not away_team:
                        home_resp = requests.get(f"{api_url}/teams/{home_team_id}", timeout=5)
                        away_resp = requests.get(f"{api_url}/teams/{away_team_id}", timeout=5)
                        if home_resp.status_code == 200:
                            home_team = home_resp.json()
                        if away_resp.status_code == 200:
                            away_team = away_resp.json()
                    
                    print(f"\n📊 Testing prediction on COMPLETED game (for accuracy):")
                    print(f"   {away_team.get('name', f'Team {away_team_id}')} @ {home_team.get('name', f'Team {home_team_id}')}")
                    print(f"   Date: {game_date}")
                    print(f"   Actual Result: {actual_winner} ({game['home_score']}-{game['away_score']})")
                else:
                    # Last resort: demo
                    print("   Using demo teams (not an actual game)")
                    home_team = teams[0]
                    away_team = teams[1]
                    home_team_id = home_team["id"]
                    away_team_id = away_team["id"]
                    game_date = (date.today() + timedelta(days=1)).isoformat()
                    season = "2024-25"
                    
                    print(f"\n📊 Testing prediction (DEMO - not a real game):")
                    print(f"   {away_team['name']} @ {home_team['name']}")
                    print(f"   Date: {game_date}")
        else:
            # Fallback to demo
            print(f"\n⚠️  Could not fetch games (status {games_response.status_code})")
            print("   Using demo teams (not an actual scheduled game)")
            home_team = teams[0]
            away_team = teams[1]
            home_team_id = home_team["id"]
            away_team_id = away_team["id"]
            game_date = (date.today() + timedelta(days=1)).isoformat()
            season = "2024-25"
            
            print(f"\n📊 Testing prediction (DEMO - not a real game):")
            print(f"   {away_team['name']} @ {home_team['name']}")
            print(f"   Date: {game_date}")
        
        print("   Making prediction request...")
        prediction_response = requests.post(
            f"{api_url}/games/predict",
            json={
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "game_date": game_date,
                "season": season
            },
            timeout=10
        )
        
        if prediction_response.status_code == 200:
            result = prediction_response.json()
            print(f"\n✅ Prediction:")
            print(f"   Winner: {result['predicted_winner'].upper()}")
            print(f"   Confidence: {result['probability']:.1%}")
            print(f"   Home Win Prob: {result['home_win_prob']:.1%}")
            print(f"   Away Win Prob: {result['away_win_prob']:.1%}")
            
            # If we tested on a completed game, show if prediction was correct
            # (actual_winner is set in the else block above)
            try:
                if 'actual_winner' in locals() and actual_winner:
                    predicted_winner = "HOME" if result['prediction'] == 1 else "AWAY"
                    correct = predicted_winner == actual_winner
                    print(f"   {'✓ CORRECT' if correct else '✗ INCORRECT'} (Actual: {actual_winner})")
            except:
                pass  # Not a completed game, skip accuracy check
        else:
            print(f"\n❌ Error: {prediction_response.status_code}")
            print(f"   Response headers: {dict(prediction_response.headers)}")
            try:
                error_detail = prediction_response.json()
                print(f"   JSON Response: {error_detail}")
                if "detail" in error_detail:
                    print(f"   Detail: {error_detail['detail']}")
                else:
                    print(f"   Full response: {error_detail}")
            except Exception as e:
                print(f"   Could not parse JSON: {e}")
                print(f"   Raw response text: {prediction_response.text[:500]}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_future_game():
    """Test prediction for a specific future game."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test prediction for a future game")
    parser.add_argument("--home-team-id", type=int, required=True)
    parser.add_argument("--away-team-id", type=int, required=True)
    parser.add_argument("--game-date", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--season", type=str, default="2024-25")
    
    args = parser.parse_args()
    
    print("🏀 Testing Future Game Prediction")
    print("=" * 50)
    
    init_db()
    db = SessionLocal()
    
    try:
        model = load_game_outcome_model()
        if not model:
            print("\n❌ No trained model found.")
            return
        
        game_date = date.fromisoformat(args.game_date)
        
        print(f"\n📊 Game Details:")
        print(f"   Home Team ID: {args.home_team_id}")
        print(f"   Away Team ID: {args.away_team_id}")
        print(f"   Date: {game_date}")
        print(f"   Season: {args.season}")
        
        features_df = prepare_features_for_prediction(
            db, args.home_team_id, args.away_team_id, game_date, args.season
        )
        
        result = predict_game_outcome(model, features_df)
        
        print(f"\n✅ Prediction:")
        print(f"   Winner: {result['predicted_winner'].upper()}")
        print(f"   Confidence: {result['probability']:.1%}")
        print(f"   Home Win Prob: {result['home_win_prob']:.1%}")
        print(f"   Away Win Prob: {result['away_win_prob']:.1%}")
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_future_game()
    else:
        print("Choose test mode:")
        print("1. Direct (no server)")
        print("2. Via API (server required)")
        
        choice = input("\nEnter choice (1 or 2): ")
        
        if choice == "1":
            test_direct()
        elif choice == "2":
            test_via_api()
        else:
            print("Invalid choice")

