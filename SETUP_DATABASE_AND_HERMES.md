# 🛠️ Database and Hermes LLM Setup Guide

This guide will walk you through setting up both the DuckDB database and Hermes LLM server for your personal finance application.

---

## 📊 Part 1: Database Setup (DuckDB)

### Prerequisites
- Python virtual environment activated
- DuckDB Python package (optional - can be skipped)

### Option A: Install DuckDB (Recommended but Optional)

```bash
# Activate your virtual environment
cd /Users/mmultra21/Documents/retro21_finance
source venv/bin/activate

# Try to install DuckDB
pip install duckdb pandas

# Note: If this fails due to compilation errors, it's okay!
# The test server works without DuckDB
```

### Option B: Skip DuckDB (Use Test Server Instead)

If DuckDB installation fails (common on some systems), you can:

```bash
# Just use the simplified test server
python test_api_server.py

# This gives you all the API functionality without database persistence
```

### Initialize the Database (If DuckDB Installed)

```bash
# Start Python
python3

# Run this code:
```

```python
import sys
sys.path.insert(0, '.')

# Import and initialize the database
from personal_finance.storage.duck import DuckDBManager

# Create database instance
db = DuckDBManager(db_path='./data/finance.db')

print("✅ Database initialized successfully!")
print(f"   Location: ./data/finance.db")
print(f"   Tables created: transactions, accounts, categories, import_logs")
print(f"   Default categories loaded")
print(f"   Indexes created for performance")

# Exit Python
exit()
```

### Verify Database Setup

```bash
# Check if database was created
ls -lh data/finance.db

# You should see a file like:
# -rw-r--r--  1 user  staff   128K Oct  3 12:34 data/finance.db
```

### Database Schema Overview

The database includes:

**Tables:**
- `transactions` - All financial transactions (denormalized for analytics)
- `accounts` - Bank accounts (checking, savings, credit cards)
- `categories` - Transaction categories (income, expenses)
- `import_logs` - History of CSV imports

**Pre-loaded Data:**
- 30+ default categories (Income:Salary, Expenses:Food, etc.)
- 5 example accounts
- Indexes for fast queries

**Views:**
- `monthly_summary` - Monthly spending by category
- `category_summary` - Total spending by category
- `account_balances` - Running account balances
- `monthly_cash_flow` - Income vs expenses by month
- `top_merchants` - Most frequent merchants

---

## 🤖 Part 2: Hermes LLM Setup

### Your Current Setup Status

✅ **llama.cpp installed:** `/Users/mmultra21/src/llama.cpp`
✅ **llama-server binary:** `/Users/mmultra21/src/llama.cpp/build/llama-server`
✅ **Hermes model:** `/Users/mmultra21/models/llama/hermes3-8b.Q4_K_M.gguf` (4.6 GB)

You're all set! Everything is already installed.

### Start Hermes LLM Server

#### Method 1: Using the Provided Script (Easiest)

```bash
cd /Users/mmultra21/Documents/retro21_finance

# Start Hermes in a dedicated terminal
./run_hermes3.sh
```

**What this does:**
- Starts llama-server on port 11434
- Loads the Hermes-3 8B model (Q4 quantized)
- Allocates 4096 token context window
- Logs output to `/tmp/llm_server.log`
- Waits until server is ready (up to 180 seconds)

**Expected output:**
```
Starting Hermes-3 server: /Users/mmultra21/src/llama.cpp/build/llama-server
Model: /Users/mmultra21/models/llama/hermes3-8b.Q4_K_M.gguf  Host: 127.0.0.1  Port: 11434
(logs: /tmp/llm_server.log)
Waiting for server to become ready (timeout 180s).....................
✅ Server ready (PID=12345). To stop: kill 12345
```

#### Method 2: Manual Start (Advanced)

```bash
# Set environment variables
export LLAMA_DIR="$HOME/src/llama.cpp"
export HERMES3_GGUF="$HOME/models/llama/hermes3-8b.Q4_K_M.gguf"

# Start server manually
$LLAMA_DIR/build/llama-server \
  -m "$HERMES3_GGUF" \
  --host 127.0.0.1 \
  --port 11434 \
  -c 4096 \
  --keep -1 \
  --mlock
```

#### Method 3: Use Mock Server (Testing Only)

```bash
# For testing without the real LLM
source venv/bin/activate
python mock_hermes_server.py

# This simulates the LLM API with pre-programmed responses
```

### Verify Hermes is Running

```bash
# Test health endpoint
curl http://127.0.0.1:11434/health

# Expected response:
# {"status":"ok"}

# Test completion endpoint
curl -X POST http://127.0.0.1:11434/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Say hello",
    "max_tokens": 50,
    "temperature": 0.7,
    "stop": ["\n"]
  }'

# Expected: JSON response with generated text
```

### Stop Hermes Server

```bash
# Method 1: Use the stop script
./stop_hermes3.sh

# Method 2: Manual stop
kill $(cat /tmp/llm_server.pid)

# Method 3: Find and kill process
lsof -i :11434
kill -9 <PID>
```

### View Hermes Logs

```bash
# Watch logs in real-time
tail -f /tmp/llm_server.log

# View last 50 lines
tail -n 50 /tmp/llm_server.log

# Search for errors
grep -i error /tmp/llm_server.log
```

---

## 🚀 Part 3: Complete Setup Workflow

### Full Stack Startup (All Components)

```bash
# Terminal 1 - Start Hermes LLM
cd /Users/mmultra21/Documents/retro21_finance
./run_hermes3.sh

# Terminal 2 - Start API Server
cd /Users/mmultra21/Documents/retro21_finance
source venv/bin/activate
python test_api_server.py
# OR if DuckDB is installed:
# cd personal-finance && python -c "import sys; sys.path.insert(0, '..'); from api.main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"

# Terminal 3 - Run tests
cd /Users/mmultra21/Documents/retro21_finance
source venv/bin/activate
python test_financial_use_case.py
```

**Expected result:** All 6 tests pass ✅

### Simplified Startup (Test Mode)

```bash
# Terminal 1 - Mock LLM (for testing)
source venv/bin/activate
python mock_hermes_server.py

# Terminal 2 - Test API Server
source venv/bin/activate
python test_api_server.py

# Terminal 3 - Run tests
source venv/bin/activate
python test_financial_use_case.py
```

---

## 🔧 Troubleshooting

### Database Issues

**Problem:** "Module 'duckdb' not found"
```bash
# Solution 1: Install DuckDB
pip install duckdb pandas

# Solution 2: Use test server (no DB required)
python test_api_server.py
```

**Problem:** "Cannot create database file"
```bash
# Create data directory
mkdir -p data

# Check permissions
ls -la data/
```

**Problem:** "Schema initialization failed"
```bash
# Check SQL file exists
ls -la personal-finance/storage/init_duckdb.sql

# Manually initialize
python -c "
from personal_finance.storage.duck import DuckDBManager
db = DuckDBManager()
print('Database initialized')
"
```

### Hermes/LLM Issues

**Problem:** "llama-server not found"
```bash
# Check if binary exists
ls -la ~/src/llama.cpp/build/llama-server

# If missing, rebuild llama.cpp:
cd ~/src/llama.cpp
mkdir -p build && cd build
cmake ..
make llama-server
```

**Problem:** "Model file not found"
```bash
# Check model location
ls -la ~/models/llama/*.gguf

# Update path in run_hermes3.sh if needed
export HERMES3_GGUF="/path/to/your/model.gguf"
```

**Problem:** "Server not becoming ready"
```bash
# Check logs
tail -f /tmp/llm_server.log

# Common issues:
# - Model file corrupted (re-download)
# - Not enough RAM (need ~6GB for 8B Q4 model)
# - Port already in use (kill existing process)

# Kill any existing llama-server
pkill -f llama-server
```

**Problem:** "Connection refused on port 11434"
```bash
# Check if server is actually running
lsof -i :11434

# Try restarting
./stop_hermes3.sh
./run_hermes3.sh
```

---

## 📈 Performance Tuning

### Hermes LLM Optimization

**For faster responses (less accurate):**
```bash
# Edit run_hermes3.sh, change context size:
-c 2048  # Instead of 4096
```

**For better quality (slower):**
```bash
# In your API calls, adjust temperature:
# Lower = more deterministic (0.1 - 0.3)
# Higher = more creative (0.7 - 1.0)
```

**For memory-constrained systems:**
```bash
# Use a smaller quantized model like Q3 or Q2
# Download from Hugging Face and update path
```

### Database Optimization

**For large transaction volumes:**
```python
# Use batch inserts
db.insert_transactions(transactions_list)  # Instead of one-by-one

# Create additional indexes
db.execute_query("CREATE INDEX idx_custom ON transactions(your_field)")
```

---

## 🎯 Quick Reference

### Start Everything
```bash
./run_hermes3.sh                    # Terminal 1
source venv/bin/activate && python test_api_server.py  # Terminal 2
```

### Stop Everything
```bash
./stop_hermes3.sh                   # Stop Hermes
# Ctrl+C in API server terminal     # Stop API
```

### Test Everything
```bash
curl http://127.0.0.1:11434/health  # Test Hermes
curl http://127.0.0.1:8000/health   # Test API
python test_financial_use_case.py   # Full test suite
```

### View Logs
```bash
tail -f /tmp/llm_server.log         # Hermes logs
# API logs appear in terminal
```

---

## 📚 Next Steps

1. ✅ Database initialized
2. ✅ Hermes LLM running
3. ✅ API server started
4. ✅ Tests passing

**Now you can:**
- Import CSV transactions: `POST /ingest/csv`
- Query financial data: `GET /analytics/summary`
- Generate narratives: `POST /narrate`
- Fill tax forms: `POST /forms/fill`

See [QUICKSTART.md](QUICKSTART.md) for API usage examples!
