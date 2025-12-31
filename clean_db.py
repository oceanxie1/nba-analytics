"""Utility script to clean/delete data from the database."""
import sys
from app.db import SessionLocal, init_db
from app.models import Team, Player, Game, BoxScore

def show_counts(db):
    """Show current record counts."""
    print("\n📊 Current Database Counts:")
    print(f"  Teams: {db.query(Team).count()}")
    print(f"  Players: {db.query(Player).count()}")
    print(f"  Games: {db.query(Game).count()}")
    print(f"  Box Scores: {db.query(BoxScore).count()}\n")

def show_sample_data(db):
    """Show sample data from each table."""
    print("\n📋 Sample Data:")
    
    teams = db.query(Team).limit(5).all()
    if teams:
        print("\n  Teams (first 5):")
        for t in teams:
            print(f"    ID {t.id}: {t.name} ({t.abbreviation})")
    
    players = db.query(Player).limit(5).all()
    if players:
        print("\n  Players (first 5):")
        for p in players:
            print(f"    ID {p.id}: {p.name} (Team ID: {p.team_id})")
    
    games = db.query(Game).order_by(Game.id).limit(5).all()
    if games:
        print("\n  Games (first 5):")
        for g in games:
            print(f"    ID {g.id}: {g.season} - {g.game_date}")

def delete_by_id(db, table_name, record_id):
    """Delete a specific record by ID, handling foreign key relationships."""
    try:
        if table_name.lower() == "team":
            record = db.query(Team).filter(Team.id == record_id).first()
            if record:
                # Delete related players first
                players = db.query(Player).filter(Player.team_id == record_id).all()
                for player in players:
                    # Delete box scores for this player
                    box_scores = db.query(BoxScore).filter(BoxScore.player_id == player.id).all()
                    for bs in box_scores:
                        db.delete(bs)
                    db.delete(player)
                
                # Delete games involving this team
                games = db.query(Game).filter(
                    (Game.home_team_id == record_id) | (Game.away_team_id == record_id)
                ).all()
                for game in games:
                    # Delete box scores for this game
                    box_scores = db.query(BoxScore).filter(BoxScore.game_id == game.id).all()
                    for bs in box_scores:
                        db.delete(bs)
                    db.delete(game)
                
                db.delete(record)
        
        elif table_name.lower() == "player":
            record = db.query(Player).filter(Player.id == record_id).first()
            if record:
                # Delete box scores for this player first
                box_scores = db.query(BoxScore).filter(BoxScore.player_id == record_id).all()
                for bs in box_scores:
                    db.delete(bs)
                db.delete(record)
        
        elif table_name.lower() == "game":
            record = db.query(Game).filter(Game.id == record_id).first()
            if record:
                # Delete box scores for this game first
                box_scores = db.query(BoxScore).filter(BoxScore.game_id == record_id).all()
                for bs in box_scores:
                    db.delete(bs)
                db.delete(record)
        
        elif table_name.lower() == "boxscore" or table_name.lower() == "box_score":
            record = db.query(BoxScore).filter(BoxScore.id == record_id).first()
            if record:
                db.delete(record)
        else:
            print(f"❌ Unknown table: {table_name}")
            return False
        
        if not record:
            print(f"❌ No {table_name} found with ID {record_id}")
            return False
        
        db.commit()
        print(f"✅ Deleted {table_name} ID {record_id}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting {table_name} ID {record_id}: {e}")
        return False

def delete_all_from_table(db, table_name):
    """Delete all records from a table, handling foreign key relationships."""
    try:
        if table_name.lower() == "team":
            # Delete in order: box_scores -> players -> games -> teams
            teams = db.query(Team).all()
            count = len(teams)
            for team in teams:
                # Delete related players and their box scores
                players = db.query(Player).filter(Player.team_id == team.id).all()
                for player in players:
                    db.query(BoxScore).filter(BoxScore.player_id == player.id).delete()
                    db.delete(player)
                # Delete games and their box scores
                games = db.query(Game).filter(
                    (Game.home_team_id == team.id) | (Game.away_team_id == team.id)
                ).all()
                for game in games:
                    db.query(BoxScore).filter(BoxScore.game_id == game.id).delete()
                    db.delete(game)
                db.delete(team)
        
        elif table_name.lower() == "player":
            # Delete box scores first, then players
            players = db.query(Player).all()
            count = len(players)
            for player in players:
                db.query(BoxScore).filter(BoxScore.player_id == player.id).delete()
                db.delete(player)
        
        elif table_name.lower() == "game":
            # Delete box scores first, then games
            games = db.query(Game).all()
            count = len(games)
            for game in games:
                db.query(BoxScore).filter(BoxScore.game_id == game.id).delete()
                db.delete(game)
        
        elif table_name.lower() == "boxscore" or table_name.lower() == "box_score":
            count = db.query(BoxScore).count()
            db.query(BoxScore).delete()
        else:
            print(f"❌ Unknown table: {table_name}")
            return False
        
        db.commit()
        print(f"✅ Deleted {count} records from {table_name}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting from {table_name}: {e}")
        return False

def clear_all_data(db):
    """Clear ALL data from the database (complete wipe)."""
    print("\n⚠️  WARNING: This will delete ALL data from the database!")
    print("   This includes teams, players, games, and box scores.")
    
    # Delete in correct order to avoid foreign key constraints
    box_score_count = db.query(BoxScore).count()
    player_count = db.query(Player).count()
    game_count = db.query(Game).count()
    team_count = db.query(Team).count()
    
    # Delete box scores first
    db.query(BoxScore).delete()
    print(f"   Deleted {box_score_count} box scores")
    
    # Delete players
    db.query(Player).delete()
    print(f"   Deleted {player_count} players")
    
    # Delete games
    db.query(Game).delete()
    print(f"   Deleted {game_count} games")
    
    # Delete teams
    db.query(Team).delete()
    print(f"   Deleted {team_count} teams")
    
    db.commit()
    
    total = box_score_count + player_count + game_count + team_count
    print(f"\n✅ Database cleared! Deleted {total} total records.")
    print("   You can now run your API ingestion to populate fresh data.")
    
    return total

def delete_sample_data(db):
    """Delete all data added by add_sample_data.py (Lakers, Warriors, Celtics, LeBron, Curry, Tatum, etc.)."""
    print("\n🗑️  Deleting sample/test data from add_sample_data.py...")
    
    deleted_counts = {"teams": 0, "players": 0, "games": 0, "box_scores": 0}
    
    # Find and delete sample teams (Lakers, Warriors, Celtics)
    sample_team_names = ["Los Angeles Lakers", "Golden State Warriors", "Boston Celtics"]
    sample_teams = db.query(Team).filter(Team.name.in_(sample_team_names)).all()
    
    for team in sample_teams:
        # Delete players on these teams (LeBron, Curry, Tatum, etc.)
        players = db.query(Player).filter(Player.team_id == team.id).all()
        for player in players:
            # Delete box scores for this player
            box_scores = db.query(BoxScore).filter(BoxScore.player_id == player.id).all()
            for bs in box_scores:
                db.delete(bs)
                deleted_counts["box_scores"] += 1
            db.delete(player)
            deleted_counts["players"] += 1
        
        # Delete games involving this team
        games = db.query(Game).filter(
            (Game.home_team_id == team.id) | (Game.away_team_id == team.id)
        ).all()
        for game in games:
            # Delete box scores for this game (in case any remain)
            box_scores = db.query(BoxScore).filter(BoxScore.game_id == game.id).all()
            for bs in box_scores:
                db.delete(bs)
                deleted_counts["box_scores"] += 1
            db.delete(game)
            deleted_counts["games"] += 1
        
        db.delete(team)
        deleted_counts["teams"] += 1
    
    # Also delete any players with those specific names (in case team_id is NULL)
    sample_player_names = ["LeBron James", "Stephen Curry", "Jayson Tatum"]
    sample_players = db.query(Player).filter(Player.name.in_(sample_player_names)).all()
    for player in sample_players:
        # Delete box scores for this player
        box_scores = db.query(BoxScore).filter(BoxScore.player_id == player.id).all()
        for bs in box_scores:
            db.delete(bs)
            deleted_counts["box_scores"] += 1
        db.delete(player)
        deleted_counts["players"] += 1
    
    db.commit()
    
    print(f"✅ Deleted sample data:")
    print(f"   Teams: {deleted_counts['teams']}")
    print(f"   Players: {deleted_counts['players']}")
    print(f"   Games: {deleted_counts['games']}")
    print(f"   Box Scores: {deleted_counts['box_scores']}")
    
    return sum(deleted_counts.values())

def delete_by_ids(db, table_name, ids):
    """Delete multiple records by IDs."""
    deleted = 0
    for record_id in ids:
        if delete_by_id(db, table_name, record_id):
            deleted += 1
    return deleted

def interactive_mode():
    """Interactive mode for cleaning the database."""
    db = SessionLocal()
    
    try:
        while True:
            show_counts(db)
            print("Options:")
            print("  1. Show sample data")
            print("  2. Delete by ID")
            print("  3. Delete all from table")
            print("  4. Delete sample/test data (Lakers, Warriors, Celtics)")
            print("  5. Delete multiple IDs")
            print("  6. Exit")
            
            choice = input("\nEnter choice (1-7): ").strip()
            
            if choice == "1":
                show_sample_data(db)
            
            elif choice == "2":
                table = input("Table name (team/player/game/boxscore): ").strip()
                try:
                    record_id = int(input("Record ID: ").strip())
                    delete_by_id(db, table, record_id)
                except ValueError:
                    print("❌ Invalid ID")
            
            elif choice == "3":
                table = input("Table name (team/player/game/boxscore): ").strip()
                confirm = input(f"⚠️  Delete ALL from {table}? (yes/no): ").strip().lower()
                if confirm == "yes":
                    delete_all_from_table(db, table)
                else:
                    print("Cancelled")
            
            elif choice == "4":
                confirm = input("⚠️  Delete sample data (Lakers, Warriors, Celtics)? (yes/no): ").strip().lower()
                if confirm == "yes":
                    delete_sample_data(db)
                else:
                    print("Cancelled")
            
            elif choice == "5":
                table = input("Table name (team/player/game/boxscore): ").strip()
                ids_str = input("Enter IDs (comma-separated, e.g., 1,2,3): ").strip()
                try:
                    ids = [int(x.strip()) for x in ids_str.split(",")]
                    deleted = delete_by_ids(db, table, ids)
                    print(f"✅ Deleted {deleted}/{len(ids)} records")
                except ValueError:
                    print("❌ Invalid IDs format")
            
            elif choice == "6":
                confirm = input("⚠️  Are you SURE you want to delete ALL data? Type 'DELETE ALL' to confirm: ").strip()
                if confirm == "DELETE ALL":
                    clear_all_data(db)
                else:
                    print("Cancelled")
            
            elif choice == "7":
                print("👋 Exiting...")
                break
            
            else:
                print("❌ Invalid choice")
            
            print()
    
    finally:
        db.close()

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command-line mode
        db = SessionLocal()
        try:
            if sys.argv[1] == "count":
                show_counts(db)
            elif sys.argv[1] == "sample":
                show_sample_data(db)
            elif sys.argv[1] == "delete" and len(sys.argv) >= 4:
                table = sys.argv[2]
                record_id = int(sys.argv[3])
                delete_by_id(db, table, record_id)
            elif sys.argv[1] == "delete-all" and len(sys.argv) >= 3:
                table = sys.argv[2]
                confirm = input(f"⚠️  Delete ALL from {table}? (yes/no): ").strip().lower()
                if confirm == "yes":
                    delete_all_from_table(db, table)
            elif sys.argv[1] == "delete-sample":
                confirm = input("⚠️  Delete sample data? (yes/no): ").strip().lower()
                if confirm == "yes":
                    delete_sample_data(db)
            elif sys.argv[1] == "clear-all":
                confirm = input("⚠️  Are you SURE you want to delete ALL data? Type 'DELETE ALL' to confirm: ").strip()
                if confirm == "DELETE ALL":
                    clear_all_data(db)
            else:
                print("Usage:")
                print("  python clean_db.py                    # Interactive mode")
                print("  python clean_db.py count               # Show counts")
                print("  python clean_db.py sample              # Show sample data")
                print("  python clean_db.py delete <table> <id>  # Delete by ID")
                print("  python clean_db.py delete-all <table> # Delete all from table")
                print("  python clean_db.py delete-sample       # Delete sample data")
                print("  python clean_db.py clear-all           # Clear ALL data (complete wipe)")
        finally:
            db.close()
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()

