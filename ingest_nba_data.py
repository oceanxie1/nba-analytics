"""Script to ingest NBA data from API into the database."""
import sys
from app.db import SessionLocal
from app.ingestion.ingest import ingest_from_nba_api


def normalize_season(season_str: str) -> str:
    """Normalize season string to format expected by NBA API (e.g., '2023-24').
    
    Handles formats like:
    - '2023-2024' -> '2023-24'
    - '2023-24' -> '2023-24' (no change)
    - '2023' -> '2023-24' (assumes current season)
    """
    if not season_str:
        return None
    
    # If already in correct format (YYYY-YY), return as-is
    if len(season_str) == 7 and season_str[4] == '-':
        return season_str
    
    # If format is YYYY-YYYY, convert to YYYY-YY
    if len(season_str) == 9 and season_str[4] == '-':
        start_year = season_str[:4]
        end_year = season_str[5:]
        return f"{start_year}-{end_year[2:]}"
    
    # If just a year, assume it's the start year
    if len(season_str) == 4 and season_str.isdigit():
        start_year = int(season_str)
        end_year = start_year + 1
        return f"{start_year}-{str(end_year)[2:]}"
    
    # Return as-is if we can't parse it
    return season_str

def main():
    """Main ingestion script."""
    if len(sys.argv) > 1:
        season_input = sys.argv[1]
        season = normalize_season(season_input)
        if season != season_input:
            print(f"📝 Converted season format: '{season_input}' -> '{season}'")
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
        ingest_from_nba_api(season=season, db=db, use_nba_api_lib=True)
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

