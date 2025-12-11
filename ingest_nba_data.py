"""Script to ingest NBA data from API into the database."""
import sys
from app.db import SessionLocal
from app.ingestion.ingest import ingest_from_nba_api


def main():
    """Main ingestion script."""
    if len(sys.argv) > 1:
        season = sys.argv[1]
    else:
        # Default to current season
        from datetime import datetime
        current_year = datetime.now().year
        if datetime.now().month >= 10:
            season = f"{current_year}-{str(current_year + 1)[2:]}"
        else:
            season = f"{current_year - 1}-{str(current_year)[2:]}"
    
    print(f"🚀 NBA Data Ingestion")
    print(f"Season: {season}")
    print()
    
    db = SessionLocal()
    try:
        ingest_from_nba_api(season=season, db=db)
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

