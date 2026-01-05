"""Test games and box scores ingestion with progress tracking."""
from app.db import SessionLocal
from app.ingestion.ingest import ingest_from_nba_api
from app.models import Team, Player, Game, BoxScore
from datetime import datetime

def test_games_boxscores(date_range_days=7):
    """Test games and box scores ingestion for a date range.
    
    Args:
        date_range_days: Number of days to test (default: 7 days for quick test)
    """
    db = SessionLocal()
    
    try:
        print("🧪 Testing Games & Box Scores Ingestion\n")
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
        
        # Run ingestion
        print("🚀 Starting ingestion...")
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
        if games_after > games_before:
            new_games = db.query(Game).order_by(Game.id.desc()).limit(5).all()
            print("✅ Sample new games:")
            for game in new_games:
                home_team = db.query(Team).filter(Team.id == game.home_team_id).first()
                away_team = db.query(Team).filter(Team.id == game.away_team_id).first()
                print(f"   - {away_team.abbreviation if away_team else '?'} @ {home_team.abbreviation if home_team else '?'} on {game.game_date} ({game.home_score}-{game.away_score})")
        
        if box_scores_after > box_scores_before:
            new_box_scores = db.query(BoxScore).order_by(BoxScore.id.desc()).limit(5).all()
            print("\n✅ Sample new box scores:")
            for bs in new_box_scores:
                player = db.query(Player).filter(Player.id == bs.player_id).first()
                game = db.query(Game).filter(Game.id == bs.game_id).first()
                print(f"   - {player.name if player else '?'}: {bs.points} pts, {bs.rebounds} reb, {bs.assists} ast (Game: {game.id if game else '?'})")
        
        # Calculate stats
        if games_after > games_before:
            total_games = games_after - games_before
            total_box_scores = box_scores_after - box_scores_before
            avg_box_scores_per_game = total_box_scores / total_games if total_games > 0 else 0
            print(f"\n📈 Stats:")
            print(f"   Average box scores per game: {avg_box_scores_per_game:.1f}")
        
        print("\n" + "=" * 60)
        print("✅ Test complete!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        print("🏀 Running FULL SEASON ingestion (this will take ~25-30 minutes)...")
        print("   Press Ctrl+C to cancel\n")
        test_games_boxscores()
    else:
        print("🧪 Running test ingestion...")
        print("   (Use 'python test_games_boxscores.py full' for full season)\n")
        test_games_boxscores()

