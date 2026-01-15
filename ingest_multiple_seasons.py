#!/usr/bin/env python3
"""Script to ingest multiple NBA seasons."""
import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, init_db
from app.ingestion.ingest import ingest_season
from app.models import Game


def get_season_string(year: int) -> str:
    """Convert year to season string (e.g., 2023 -> '2023-24')."""
    next_year = (year % 100) + 1
    return f"{year}-{next_year:02d}"


def main():
    """Ingest multiple seasons."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest multiple NBA seasons")
    parser.add_argument(
        "--start-year",
        type=int,
        help="Start year (e.g., 2020 for 2020-21 season)"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        help="End year (inclusive, e.g., 2023 for 2023-24 season)"
    )
    parser.add_argument(
        "--seasons",
        type=str,
        nargs="+",
        help="Specific seasons to ingest (e.g., '2020-21' '2021-22')"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip seasons that already have data (default: True)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Delay between season ingestions in seconds (default: 5.0)"
    )
    
    args = parser.parse_args()
    
    print("🏀 NBA Data Ingestion - Multiple Seasons")
    print("=" * 50)
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        # Determine which seasons to ingest
        seasons_to_ingest = []
        
        if args.seasons:
            seasons_to_ingest = args.seasons
        elif args.start_year and args.end_year:
            for year in range(args.start_year, args.end_year + 1):
                seasons_to_ingest.append(get_season_string(year))
        else:
            print("\n❌ Error: Must specify either --seasons or --start-year and --end-year")
            parser.print_help()
            return 1
        
        print(f"\n📅 Seasons to ingest: {', '.join(seasons_to_ingest)}")
        
        # Check existing seasons if skip-existing is enabled
        if args.skip_existing:
            existing_seasons = set()
            for season in seasons_to_ingest:
                game_count = db.query(Game).filter(Game.season == season).count()
                if game_count > 0:
                    existing_seasons.add(season)
            
            if existing_seasons:
                print(f"\n⚠️  Found existing data for: {', '.join(existing_seasons)}")
                seasons_to_ingest = [s for s in seasons_to_ingest if s not in existing_seasons]
                
                if not seasons_to_ingest:
                    print("✅ All seasons already have data. Nothing to ingest.")
                    return 0
                
                print(f"📝 Will ingest: {', '.join(seasons_to_ingest)}")
        
        # Ingest each season
        total_seasons = len(seasons_to_ingest)
        for idx, season in enumerate(seasons_to_ingest, 1):
            print(f"\n{'=' * 50}")
            print(f"Season {idx}/{total_seasons}: {season}")
            print(f"{'=' * 50}")
            
            try:
                start_time = time.time()
                result = ingest_season(db, season)
                elapsed = time.time() - start_time
                
                if result["success"]:
                    print(f"\n✅ Successfully ingested {season}")
                    print(f"   Games: {result.get('games_added', 0)}")
                    print(f"   Box Scores: {result.get('box_scores_added', 0)}")
                    print(f"   Time: {elapsed:.1f}s")
                else:
                    print(f"\n⚠️  Partial ingestion for {season}")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                    print(f"   Games: {result.get('games_added', 0)}")
                    print(f"   Box Scores: {result.get('box_scores_added', 0)}")
                
            except Exception as e:
                print(f"\n❌ Error ingesting {season}: {e}")
                import traceback
                traceback.print_exc()
            
            # Delay between seasons (except for the last one)
            if idx < total_seasons and args.delay > 0:
                print(f"\n⏳ Waiting {args.delay}s before next season...")
                time.sleep(args.delay)
        
        print(f"\n{'=' * 50}")
        print("✅ Ingestion complete!")
        print(f"{'=' * 50}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ingestion interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    exit(main())



