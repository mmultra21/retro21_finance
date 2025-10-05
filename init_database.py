#!/usr/bin/env python3
"""
Simple database initialization script
Creates and initializes the DuckDB database with schema and default data
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def init_database():
    """Initialize the database."""
    print("🔧 Initializing Personal Finance Database")
    print("=" * 60)

    # Check if DuckDB is available
    try:
        import duckdb
        print("✅ DuckDB module found")
    except ImportError:
        print("❌ DuckDB not installed")
        print("\n📦 Install with: pip install duckdb pandas")
        print("\n⚠️  Alternative: Use test_api_server.py (no database required)")
        return False

    try:
        # Add personal-finance directory to path (handle hyphenated name)
        personal_finance_dir = Path(__file__).parent / 'personal-finance'
        sys.path.insert(0, str(personal_finance_dir))

        # Import the database manager
        from storage.duck import DuckDBManager

        # Create data directory if it doesn't exist
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(exist_ok=True)
        print(f"✅ Data directory: {data_dir}")

        # Initialize database
        db_path = data_dir / 'finance.db'
        print(f"\n📊 Creating database: {db_path}")

        db = DuckDBManager(db_path=str(db_path))

        print("\n✅ Database initialized successfully!")
        print(f"   Location: {db_path}")
        print(f"   Size: {db_path.stat().st_size / 1024:.1f} KB")

        # Display schema info
        print("\n📋 Database Schema:")

        tables = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        print(f"   Tables ({len(tables)}):")
        for table in tables:
            count = db.execute_query(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
            print(f"   - {table[0]:20s} ({count} records)")

        # Display views
        views = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        ).fetchall()

        if views:
            print(f"\n   Views ({len(views)}):")
            for view in views:
                print(f"   - {view[0]}")

        # Display sample categories
        print("\n📁 Sample Categories:")
        categories = db.execute_query(
            "SELECT category_name, category_type FROM categories LIMIT 10"
        ).fetchall()

        for cat in categories[:5]:
            print(f"   - {cat[0]:40s} [{cat[1]}]")
        print(f"   ... and {len(categories) - 5} more")

        print("\n🎉 Database ready to use!")
        print("\n📝 Next steps:")
        print("   1. Start API server: python test_api_server.py")
        print("   2. Import transactions: POST /ingest/csv")
        print("   3. View analytics: GET /analytics/summary")

        db.close()
        return True

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database():
    """Check if database already exists and show info."""
    data_dir = Path(__file__).parent / 'data'
    db_path = data_dir / 'finance.db'

    if db_path.exists():
        print(f"\n📊 Database already exists: {db_path}")
        print(f"   Size: {db_path.stat().st_size / 1024:.1f} KB")
        print(f"\n   To reinitialize, delete the file first:")
        print(f"   rm {db_path}")
        return True
    return False

if __name__ == "__main__":
    print()

    # Check if database exists
    if check_database():
        response = input("\n⚠️  Reinitialize database? This will delete existing data (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
        else:
            # Delete existing database
            data_dir = Path(__file__).parent / 'data'
            db_path = data_dir / 'finance.db'
            db_path.unlink()
            print(f"✅ Deleted {db_path}")

    # Initialize
    success = init_database()
    sys.exit(0 if success else 1)
