"""Quick script to check database contents."""
import sys
from sqlalchemy import create_engine, text
from app.db import DATABASE_URL

def check_database():
    """Check what's in the database."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if tables exist
        if "sqlite" in DATABASE_URL:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        else:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
        
        tables = [row[0] for row in result]
        print(f"📊 Tables in database: {', '.join(tables) if tables else 'None'}\n")
        
        # Count records in each table
        for table in tables:
            try:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                print(f"  {table}: {count} records")
            except Exception as e:
                print(f"  {table}: Error - {e}")
        
        # Show sample data if any exists
        print("\n📋 Sample data:")
        for table in tables:
            try:
                sample = conn.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                rows = sample.fetchall()
                if rows:
                    print(f"\n  {table} (first {len(rows)} rows):")
                    for row in rows:
                        print(f"    {dict(row._mapping)}")
            except Exception as e:
                pass

if __name__ == "__main__":
    check_database()

