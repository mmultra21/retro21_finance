#!/usr/bin/env python3
"""Initialize documents schema in the database."""

import sys
from pathlib import Path

# Add personal-finance to path
sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))

from storage.duck import DuckDBManager

def main():
    db_path = Path(__file__).parent / 'data' / 'finance.db'
    schema_file = Path(__file__).parent / 'personal-finance' / 'storage' / 'init_documents.sql'

    print(f"Initializing documents schema in {db_path}...")

    # Read schema
    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    # Execute schema
    db = DuckDBManager(db_path=str(db_path))

    # Split and execute each statement
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

    for statement in statements:
        if statement:
            try:
                db.execute_query(statement)
                print(f"✓ Executed: {statement[:50]}...")
            except Exception as e:
                print(f"✗ Error: {e}")

    db.close()
    print("\n✅ Documents schema initialized successfully!")

if __name__ == "__main__":
    main()
