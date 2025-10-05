# 📝 Data Management Guide

How to modify, delete, and manage your financial data in the Personal Finance application.

---

## 🗄️ **Where Your Data is Stored**

### **Database File:**
```
/Users/mmultra21/Documents/retro21_finance/data/finance.db
```

This is a DuckDB database file containing:
- **transactions** - All your financial transactions
- **accounts** - Your bank accounts
- **categories** - Expense/income categories
- **import_logs** - History of CSV imports

---

## 🔧 **Method 1: Using Python/SQL (Direct Database Access)**

### **View All Transactions**

```python
# Start Python
python3

# Connect to database
import duckdb
conn = duckdb.connect('data/finance.db')

# View all transactions
result = conn.execute("SELECT * FROM transactions LIMIT 10").fetchdf()
print(result)

# Count total transactions
count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
print(f"Total transactions: {count}")
```

### **Delete Specific Transaction**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

# Delete by transaction ID
conn.execute("DELETE FROM transactions WHERE transaction_id = 'your-id-here'")

# Delete by date range
conn.execute("DELETE FROM transactions WHERE date BETWEEN '2024-01-01' AND '2024-01-31'")

# Delete by merchant
conn.execute("DELETE FROM transactions WHERE merchant = 'Starbucks'")

# Delete by amount
conn.execute("DELETE FROM transactions WHERE amount < -100")

conn.close()
```

### **Update/Modify Transaction**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

# Update category for a transaction
conn.execute("""
    UPDATE transactions
    SET category = 'Expenses:Food:Restaurants'
    WHERE merchant = 'Chipotle'
""")

# Update amount
conn.execute("""
    UPDATE transactions
    SET amount = -125.00
    WHERE transaction_id = 'your-id-here'
""")

# Update description
conn.execute("""
    UPDATE transactions
    SET description = 'Monthly subscription'
    WHERE merchant LIKE '%Netflix%'
""")

conn.close()
```

### **Delete All Transactions**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

# Delete all transactions (CAREFUL!)
conn.execute("DELETE FROM transactions")

# Verify
count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
print(f"Remaining transactions: {count}")

conn.close()
```

---

## 🗑️ **Method 2: Delete Entire Database**

### **Start Fresh (Nuclear Option)**

```bash
# Backup first (optional)
cp data/finance.db data/finance.db.backup

# Delete database
rm data/finance.db

# Recreate from scratch
python init_database.py
```

---

## 🔍 **Method 3: Using DuckDB CLI**

### **Interactive SQL Queries**

```bash
# Install DuckDB CLI (if not installed)
brew install duckdb  # macOS
# OR download from https://duckdb.org/

# Open database
duckdb data/finance.db

# Now you're in SQL mode
```

**Inside DuckDB CLI:**

```sql
-- View all tables
SHOW TABLES;

-- View transactions
SELECT * FROM transactions LIMIT 10;

-- Count transactions
SELECT COUNT(*) FROM transactions;

-- Delete specific transactions
DELETE FROM transactions WHERE merchant = 'Starbucks';

-- Update category
UPDATE transactions
SET category = 'Expenses:Food:Coffee'
WHERE merchant LIKE '%Starbucks%';

-- View by date
SELECT date, merchant, amount, category
FROM transactions
WHERE date >= '2024-01-01'
ORDER BY date DESC;

-- Delete old transactions
DELETE FROM transactions WHERE date < '2023-01-01';

-- Exit
.quit
```

---

## 🌐 **Method 4: Via API (Programmatic)**

### **I'll create API endpoints for you:**

Let me add DELETE and UPDATE endpoints to your API...

### **Delete Transaction (Future Endpoint)**

```bash
# Delete by ID
curl -X DELETE "http://127.0.0.1:8000/transactions/{transaction_id}"

# Delete by criteria
curl -X POST "http://127.0.0.1:8000/transactions/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant": "Starbucks",
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
  }'
```

### **Update Transaction (Future Endpoint)**

```bash
curl -X PUT "http://127.0.0.1:8000/transactions/{transaction_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Expenses:Food:Coffee",
    "description": "Updated description"
  }'
```

---

## 🎨 **Method 5: Web UI (I'll Create This Now)**

I'll add a **"Manage Data"** tab to your web interface with:
- View all transactions in a table
- Edit transaction details
- Delete individual transactions
- Bulk delete options
- Search and filter

---

## 📊 **Common Data Management Tasks**

### **1. Re-categorize Transactions**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

# Change all Starbucks to Coffee category
conn.execute("""
    UPDATE transactions
    SET category = 'Expenses:Food:Coffee'
    WHERE merchant LIKE '%Starbucks%'
""")

# Change all Amazon to Shopping
conn.execute("""
    UPDATE transactions
    SET category = 'Expenses:Shopping:Online'
    WHERE merchant LIKE '%Amazon%'
""")

conn.close()
```

### **2. Clean Up Duplicate Transactions**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

# Find duplicates
duplicates = conn.execute("""
    SELECT date, merchant, amount, COUNT(*) as count
    FROM transactions
    GROUP BY date, merchant, amount
    HAVING COUNT(*) > 1
""").fetchdf()

print(duplicates)

# Delete duplicates (keep one)
conn.execute("""
    DELETE FROM transactions
    WHERE transaction_id NOT IN (
        SELECT MIN(transaction_id)
        FROM transactions
        GROUP BY date, merchant, amount
    )
""")

conn.close()
```

### **3. Archive Old Transactions**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

# Export to CSV before deleting
conn.execute("""
    COPY (
        SELECT * FROM transactions
        WHERE date < '2023-01-01'
    ) TO 'data/archive_2022.csv' (HEADER, DELIMITER ',')
""")

# Delete old transactions
conn.execute("DELETE FROM transactions WHERE date < '2023-01-01'")

conn.close()
```

### **4. Reset Categories to Default**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

# Reset all categories
conn.execute("UPDATE transactions SET category = NULL")

# OR reset to 'Uncategorized'
conn.execute("UPDATE transactions SET category = 'Expenses:Other:Uncategorized'")

conn.close()
```

---

## 🛡️ **Safety Best Practices**

### **1. Always Backup First**

```bash
# Create backup before major changes
cp data/finance.db data/finance.db.backup.$(date +%Y%m%d)

# List backups
ls -lh data/finance.db.backup.*
```

### **2. Test Queries with SELECT First**

```python
# WRONG - Delete without checking
conn.execute("DELETE FROM transactions WHERE merchant = 'Starbucks'")

# RIGHT - Check what will be deleted first
preview = conn.execute("""
    SELECT * FROM transactions WHERE merchant = 'Starbucks'
""").fetchdf()
print(f"Will delete {len(preview)} transactions")
print(preview)

# Then delete if it looks right
conn.execute("DELETE FROM transactions WHERE merchant = 'Starbucks'")
```

### **3. Use Transactions (BEGIN/COMMIT)**

```python
import duckdb
conn = duckdb.connect('data/finance.db')

try:
    conn.execute("BEGIN TRANSACTION")

    # Your changes
    conn.execute("DELETE FROM transactions WHERE amount = 0")
    conn.execute("UPDATE transactions SET category = 'Fixed' WHERE category IS NULL")

    # Commit if everything looks good
    conn.execute("COMMIT")
    print("Changes committed successfully")
except Exception as e:
    # Rollback on error
    conn.execute("ROLLBACK")
    print(f"Error: {e}. Changes rolled back.")

conn.close()
```

---

## 🔧 **Quick Reference Commands**

### **View Data**
```python
import duckdb
conn = duckdb.connect('data/finance.db')

# All transactions
conn.execute("SELECT * FROM transactions").fetchdf()

# Recent transactions
conn.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT 10").fetchdf()

# By merchant
conn.execute("SELECT * FROM transactions WHERE merchant LIKE '%Target%'").fetchdf()

# By date range
conn.execute("SELECT * FROM transactions WHERE date BETWEEN '2024-01-01' AND '2024-12-31'").fetchdf()
```

### **Delete Data**
```python
# By ID
conn.execute("DELETE FROM transactions WHERE transaction_id = 'xxx'")

# By merchant
conn.execute("DELETE FROM transactions WHERE merchant = 'Starbucks'")

# By date
conn.execute("DELETE FROM transactions WHERE date < '2023-01-01'")

# All transactions
conn.execute("DELETE FROM transactions")
```

### **Update Data**
```python
# Update category
conn.execute("UPDATE transactions SET category = 'Food' WHERE merchant = 'Chipotle'")

# Update amount
conn.execute("UPDATE transactions SET amount = -100 WHERE transaction_id = 'xxx'")

# Update multiple fields
conn.execute("""
    UPDATE transactions
    SET category = 'Shopping', description = 'Online purchase'
    WHERE merchant = 'Amazon'
""")
```

---

## 📝 **Next Steps**

I can create:

1. **Web UI for Data Management** - Add a "Manage Data" tab with:
   - Transaction table with edit/delete buttons
   - Search and filter
   - Bulk operations
   - Export to CSV

2. **API Endpoints** - Add REST endpoints for:
   - `PUT /transactions/{id}` - Update transaction
   - `DELETE /transactions/{id}` - Delete transaction
   - `POST /transactions/bulk-delete` - Delete multiple
   - `GET /transactions/search` - Advanced search

Would you like me to create these features now?

---

## 🆘 **Emergency Recovery**

### **If you accidentally deleted everything:**

```bash
# Restore from backup
cp data/finance.db.backup data/finance.db

# If no backup, reinitialize
python init_database.py
```

### **If database is corrupted:**

```bash
# Try to recover
duckdb data/finance.db "VACUUM"

# If that fails, start fresh
rm data/finance.db
python init_database.py
```

---

## 📚 **Resources**

- **DuckDB SQL Reference:** https://duckdb.org/docs/sql/introduction
- **Python DuckDB API:** https://duckdb.org/docs/api/python
- **Your Database Schema:** See `personal-finance/storage/init_duckdb.sql`

---

**Let me know if you want me to create the Web UI for data management or add the API endpoints!** 🚀
