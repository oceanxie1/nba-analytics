"""Add sample data to the database for testing."""
from datetime import date
from app.db import SessionLocal, init_db
from app.models import Team, Player, Game, BoxScore

def add_sample_data():
    """Add sample NBA data."""
    # Initialize database
    init_db()
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Team).count() > 0:
            print("⚠️  Database already has data. Skipping...")
            return
        
        # Add teams
        print("Adding teams...")
        lakers = Team(
            name="Los Angeles Lakers",
            abbreviation="LAL",
            city="Los Angeles",
            conference="West",
            division="Pacific"
        )
        warriors = Team(
            name="Golden State Warriors",
            abbreviation="GSW",
            city="San Francisco",
            conference="West",
            division="Pacific"
        )
        celtics = Team(
            name="Boston Celtics",
            abbreviation="BOS",
            city="Boston",
            conference="East",
            division="Atlantic"
        )
        
        db.add_all([lakers, warriors, celtics])
        db.commit()
        db.refresh(lakers)
        db.refresh(warriors)
        db.refresh(celtics)
        print(f"✓ Added 3 teams")
        
        # Add players
        print("Adding players...")
        lebron = Player(
            name="LeBron James",
            position="SF",
            height="6-9",
            weight=250,
            birth_date=date(1984, 12, 30),
            team_id=lakers.id
        )
        curry = Player(
            name="Stephen Curry",
            position="PG",
            height="6-2",
            weight=185,
            birth_date=date(1988, 3, 14),
            team_id=warriors.id
        )
        tatum = Player(
            name="Jayson Tatum",
            position="SF",
            height="6-8",
            weight=210,
            birth_date=date(1998, 3, 3),
            team_id=celtics.id
        )
        
        db.add_all([lebron, curry, tatum])
        db.commit()
        db.refresh(lebron)
        db.refresh(curry)
        db.refresh(tatum)
        print(f"✓ Added 3 players")
        
        # Add a game
        print("Adding games...")
        game1 = Game(
            game_date=date(2024, 1, 15),
            season="2023-24",
            home_team_id=lakers.id,
            away_team_id=warriors.id,
            home_score=120,
            away_score=115
        )
        db.add(game1)
        db.commit()
        db.refresh(game1)
        print(f"✓ Added 1 game")
        
        # Add box scores
        print("Adding box scores...")
        box1 = BoxScore(
            game_id=game1.id,
            player_id=lebron.id,
            minutes=38.5,
            points=32,
            rebounds=8,
            assists=12,
            steals=2,
            blocks=1,
            turnovers=3,
            personal_fouls=2,
            field_goals_made=12,
            field_goals_attempted=22,
            three_pointers_made=3,
            three_pointers_attempted=7,
            free_throws_made=5,
            free_throws_attempted=6,
            plus_minus=15
        )
        box2 = BoxScore(
            game_id=game1.id,
            player_id=curry.id,
            minutes=36.0,
            points=28,
            rebounds=5,
            assists=8,
            steals=1,
            blocks=0,
            turnovers=4,
            personal_fouls=3,
            field_goals_made=10,
            field_goals_attempted=20,
            three_pointers_made=6,
            three_pointers_attempted=12,
            free_throws_made=2,
            free_throws_attempted=2,
            plus_minus=-8
        )
        
        db.add_all([box1, box2])
        db.commit()
        print(f"✓ Added 2 box scores")
        
        print("\n✅ Sample data added successfully!")
        print(f"   Teams: {db.query(Team).count()}")
        print(f"   Players: {db.query(Player).count()}")
        print(f"   Games: {db.query(Game).count()}")
        print(f"   Box Scores: {db.query(BoxScore).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()

