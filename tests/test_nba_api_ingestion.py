"""Test NBA API ingestion with nba_api library."""
from app.db import SessionLocal
from app.ingestion.ingest import ingest_from_nba_api
from app.models import Team, Player, Game, BoxScore

def test_ingestion():
    """Test full ingestion process."""
    db = SessionLocal()
    
    try:
        print("🧪 Testing NBA API Ingestion\n")
        print("=" * 60)
        
        # Count before
        teams_before = db.query(Team).count()
        players_before = db.query(Player).count()
        games_before = db.query(Game).count()
        box_scores_before = db.query(BoxScore).count()
        
        print(f"📊 Before ingestion:")
        print(f"   Teams: {teams_before}")
        print(f"   Players: {players_before}")
        print(f"   Games: {games_before}")
        print(f"   Box Scores: {box_scores_before}")
        print()
        
        # Run ingestion (using nba_api library)
        print("🚀 Starting ingestion with nba_api library...")
        print("-" * 60)
        ingest_from_nba_api(season="2023-24", db=db, use_nba_api_lib=True)
        print("-" * 60)
        print()
        
        # Count after
        teams_after = db.query(Team).count()
        players_after = db.query(Player).count()
        games_after = db.query(Game).count()
        box_scores_after = db.query(BoxScore).count()
        
        print(f"📊 After ingestion:")
        print(f"   Teams: {teams_after} (+{teams_after - teams_before})")
        print(f"   Players: {players_after} (+{players_after - players_before})")
        print(f"   Games: {games_after} (+{games_after - games_before})")
        print(f"   Box Scores: {box_scores_after} (+{box_scores_after - box_scores_before})")
        print()
        
        # Show sample data
        if teams_after > teams_before:
            new_teams = db.query(Team).order_by(Team.id.desc()).limit(3).all()
            print("✅ Sample new teams:")
            for team in new_teams:
                print(f"   - {team.name} ({team.abbreviation})")
        
        if players_after > players_before:
            new_players = db.query(Player).order_by(Player.id.desc()).limit(3).all()
            print("\n✅ Sample new players:")
            for player in new_players:
                print(f"   - {player.name} ({player.position or 'N/A'})")
        
        print("\n" + "=" * 60)
        print("✅ Test complete!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_ingestion()

