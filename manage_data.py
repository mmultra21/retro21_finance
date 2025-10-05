#!/usr/bin/env python3
"""
Simple Data Management Tool for Personal Finance Database
Interactive CLI for viewing, editing, and deleting transactions
"""

import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))

def main_menu():
    """Display main menu."""
    print("\n" + "="*60)
    print("💰 Personal Finance - Data Management Tool")
    print("="*60)
    print("\n1. View Transactions")
    print("2. Search Transactions")
    print("3. Delete Transaction(s)")
    print("4. Update Transaction")
    print("5. View Statistics")
    print("6. Export to CSV")
    print("7. Clear All Data (Dangerous!)")
    print("8. Backup Database")
    print("9. Exit")
    print()

def view_transactions(db):
    """View recent transactions."""
    limit = input("How many transactions to show? (default: 10): ") or "10"

    try:
        result = db.execute_query(
            f"SELECT transaction_id, date, merchant, amount, category FROM transactions ORDER BY date DESC LIMIT {limit}"
        ).fetchdf()

        if len(result) == 0:
            print("\n📭 No transactions found.")
        else:
            print(f"\n📊 Showing {len(result)} most recent transactions:")
            print(result.to_string())
    except Exception as e:
        print(f"\n❌ Error: {e}")

def search_transactions(db):
    """Search transactions."""
    print("\nSearch by:")
    print("1. Merchant name")
    print("2. Date range")
    print("3. Category")
    print("4. Amount range")

    choice = input("\nChoice (1-4): ")

    try:
        if choice == "1":
            merchant = input("Merchant name (partial match): ")
            result = db.execute_query(
                "SELECT * FROM transactions WHERE merchant LIKE ? ORDER BY date DESC",
                [f"%{merchant}%"]
            ).fetchdf()

        elif choice == "2":
            start = input("Start date (YYYY-MM-DD): ")
            end = input("End date (YYYY-MM-DD): ")
            result = db.execute_query(
                "SELECT * FROM transactions WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                [start, end]
            ).fetchdf()

        elif choice == "3":
            category = input("Category (partial match): ")
            result = db.execute_query(
                "SELECT * FROM transactions WHERE category LIKE ? ORDER BY date DESC",
                [f"%{category}%"]
            ).fetchdf()

        elif choice == "4":
            min_amt = float(input("Minimum amount: "))
            max_amt = float(input("Maximum amount: "))
            result = db.execute_query(
                "SELECT * FROM transactions WHERE amount BETWEEN ? AND ? ORDER BY date DESC",
                [min_amt, max_amt]
            ).fetchdf()
        else:
            print("Invalid choice.")
            return

        if len(result) == 0:
            print("\n📭 No transactions found.")
        else:
            print(f"\n📊 Found {len(result)} transactions:")
            print(result.to_string())

    except Exception as e:
        print(f"\n❌ Error: {e}")

def delete_transactions(db):
    """Delete transactions."""
    print("\nDelete by:")
    print("1. Transaction ID")
    print("2. Merchant name")
    print("3. Date range")
    print("4. All transactions (DANGEROUS!)")

    choice = input("\nChoice (1-4): ")

    try:
        if choice == "1":
            txn_id = input("Transaction ID: ")

            # Preview
            preview = db.execute_query(
                "SELECT * FROM transactions WHERE transaction_id = ?",
                [txn_id]
            ).fetchdf()

            if len(preview) == 0:
                print("\n❌ Transaction not found.")
                return

            print("\n📋 Will delete:")
            print(preview.to_string())

            confirm = input("\nConfirm delete? (yes/no): ")
            if confirm.lower() == 'yes':
                db.execute_query("DELETE FROM transactions WHERE transaction_id = ?", [txn_id])
                print("✅ Transaction deleted.")
            else:
                print("❌ Cancelled.")

        elif choice == "2":
            merchant = input("Merchant name: ")

            # Preview
            preview = db.execute_query(
                "SELECT * FROM transactions WHERE merchant LIKE ?",
                [f"%{merchant}%"]
            ).fetchdf()

            if len(preview) == 0:
                print("\n❌ No transactions found.")
                return

            print(f"\n📋 Will delete {len(preview)} transactions:")
            print(preview.to_string())

            confirm = input("\nConfirm delete? (yes/no): ")
            if confirm.lower() == 'yes':
                db.execute_query("DELETE FROM transactions WHERE merchant LIKE ?", [f"%{merchant}%"])
                print(f"✅ Deleted {len(preview)} transactions.")
            else:
                print("❌ Cancelled.")

        elif choice == "3":
            start = input("Start date (YYYY-MM-DD): ")
            end = input("End date (YYYY-MM-DD): ")

            # Preview
            preview = db.execute_query(
                "SELECT * FROM transactions WHERE date BETWEEN ? AND ?",
                [start, end]
            ).fetchdf()

            if len(preview) == 0:
                print("\n❌ No transactions found.")
                return

            print(f"\n📋 Will delete {len(preview)} transactions:")
            print(preview[['date', 'merchant', 'amount', 'category']].to_string())

            confirm = input("\nConfirm delete? (yes/no): ")
            if confirm.lower() == 'yes':
                db.execute_query("DELETE FROM transactions WHERE date BETWEEN ? AND ?", [start, end])
                print(f"✅ Deleted {len(preview)} transactions.")
            else:
                print("❌ Cancelled.")

        elif choice == "4":
            count = db.execute_query("SELECT COUNT(*) FROM transactions").fetchone()[0]
            print(f"\n⚠️  WARNING: This will delete ALL {count} transactions!")
            confirm = input("Type 'DELETE ALL' to confirm: ")

            if confirm == 'DELETE ALL':
                db.execute_query("DELETE FROM transactions")
                print("✅ All transactions deleted.")
            else:
                print("❌ Cancelled.")

    except Exception as e:
        print(f"\n❌ Error: {e}")

def update_transaction(db):
    """Update a transaction."""
    txn_id = input("Transaction ID to update: ")

    # Check if exists
    preview = db.execute_query(
        "SELECT * FROM transactions WHERE transaction_id = ?",
        [txn_id]
    ).fetchdf()

    if len(preview) == 0:
        print("\n❌ Transaction not found.")
        return

    print("\n📋 Current transaction:")
    print(preview.to_string())

    print("\nWhat to update?")
    print("1. Category")
    print("2. Description")
    print("3. Amount")
    print("4. Merchant")

    choice = input("\nChoice (1-4): ")

    try:
        if choice == "1":
            new_value = input("New category: ")
            db.execute_query(
                "UPDATE transactions SET category = ? WHERE transaction_id = ?",
                [new_value, txn_id]
            )
            print("✅ Category updated.")

        elif choice == "2":
            new_value = input("New description: ")
            db.execute_query(
                "UPDATE transactions SET description = ? WHERE transaction_id = ?",
                [new_value, txn_id]
            )
            print("✅ Description updated.")

        elif choice == "3":
            new_value = float(input("New amount: "))
            db.execute_query(
                "UPDATE transactions SET amount = ? WHERE transaction_id = ?",
                [new_value, txn_id]
            )
            print("✅ Amount updated.")

        elif choice == "4":
            new_value = input("New merchant name: ")
            db.execute_query(
                "UPDATE transactions SET merchant = ? WHERE transaction_id = ?",
                [new_value, txn_id]
            )
            print("✅ Merchant updated.")

        else:
            print("Invalid choice.")

    except Exception as e:
        print(f"\n❌ Error: {e}")

def view_statistics(db):
    """View database statistics."""
    try:
        total = db.execute_query("SELECT COUNT(*) FROM transactions").fetchone()[0]
        print(f"\n📊 Total Transactions: {total}")

        if total > 0:
            # Date range
            date_range = db.execute_query(
                "SELECT MIN(date) as min_date, MAX(date) as max_date FROM transactions"
            ).fetchone()
            print(f"📅 Date Range: {date_range[0]} to {date_range[1]}")

            # Total amounts
            totals = db.execute_query("""
                SELECT
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses,
                    SUM(amount) as net
                FROM transactions
            """).fetchone()
            print(f"💵 Total Income: ${totals[0]:,.2f}")
            print(f"💸 Total Expenses: ${totals[1]:,.2f}")
            print(f"💰 Net: ${totals[2]:,.2f}")

            # Top merchants
            top_merchants = db.execute_query("""
                SELECT merchant, COUNT(*) as count, SUM(amount) as total
                FROM transactions
                WHERE merchant IS NOT NULL
                GROUP BY merchant
                ORDER BY count DESC
                LIMIT 5
            """).fetchdf()
            print("\n🏪 Top 5 Merchants:")
            print(top_merchants.to_string())

    except Exception as e:
        print(f"\n❌ Error: {e}")

def export_to_csv(db):
    """Export transactions to CSV."""
    filename = input("Filename (default: transactions_export.csv): ") or "transactions_export.csv"

    try:
        db.execute_query(f"""
            COPY (SELECT * FROM transactions ORDER BY date DESC)
            TO '{filename}' (HEADER, DELIMITER ',')
        """)
        print(f"\n✅ Exported to {filename}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def backup_database():
    """Backup database file."""
    import shutil
    from datetime import datetime

    db_path = Path("data/finance.db")
    if not db_path.exists():
        print("\n❌ Database not found.")
        return

    backup_name = f"data/finance.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        shutil.copy2(db_path, backup_name)
        print(f"\n✅ Backup created: {backup_name}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():
    """Main function."""
    # Check if database exists
    db_path = Path("data/finance.db")
    if not db_path.exists():
        print("\n❌ Database not found at data/finance.db")
        print("   Run: python init_database.py")
        sys.exit(1)

    # Try to import DuckDB manager
    try:
        from storage.duck import DuckDBManager
        db = DuckDBManager(db_path=str(db_path))
    except ImportError:
        print("\n❌ DuckDB not installed.")
        print("   Install with: pip install duckdb pandas")
        sys.exit(1)

    # Main loop
    while True:
        main_menu()
        choice = input("Choose an option (1-9): ")

        if choice == "1":
            view_transactions(db)
        elif choice == "2":
            search_transactions(db)
        elif choice == "3":
            delete_transactions(db)
        elif choice == "4":
            update_transaction(db)
        elif choice == "5":
            view_statistics(db)
        elif choice == "6":
            export_to_csv(db)
        elif choice == "7":
            count = db.execute_query("SELECT COUNT(*) FROM transactions").fetchone()[0]
            print(f"\n⚠️  WARNING: Delete ALL {count} transactions?")
            confirm = input("Type 'DELETE ALL' to confirm: ")
            if confirm == 'DELETE ALL':
                db.execute_query("DELETE FROM transactions")
                print("✅ All data cleared.")
            else:
                print("❌ Cancelled.")
        elif choice == "8":
            backup_database()
        elif choice == "9":
            print("\n👋 Goodbye!")
            db.close()
            break
        else:
            print("\n❌ Invalid choice. Please try again.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
