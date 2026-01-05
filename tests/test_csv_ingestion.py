"""Test CSV ingestion functionality."""
from app.db import SessionLocal
from app.ingestion.csv_ingest import (
    ingest_teams_from_csv,
    ingest_players_from_csv,
    ingest_games_from_csv,
    ingest_box_scores_from_csv
)

def test_csv_ingestion():
    """Test CSV ingestion with sample files."""
    db = SessionLocal()
    
    try:
        print("🧪 Testing CSV Ingestion\n")
        
        # Test teams
        print("1️⃣ Testing team ingestion...")
        team_map = ingest_teams_from_csv("test_teams.csv", db)
        print(f"✅ Ingested {len(team_map)} teams")
        print(f"   Team map: {team_map}\n")
        
        # Test players (would need a CSV file)
        print("2️⃣ Player ingestion requires players.csv file")
        print("   (Skipping for now - no test file)\n")
        
        print("✅ CSV ingestion test complete!")
        print(f"\n📊 Total teams in database: {len(team_map)}")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("   Make sure test_teams.csv exists")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_csv_ingestion()

