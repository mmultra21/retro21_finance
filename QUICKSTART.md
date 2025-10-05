# 🚀 Quick Start Guide - Personal Finance Application

## Easiest Way to Get Started (2 Steps)

### Step 1: Install Dependencies
```bash
# Make sure you're in the retro21_finance directory
cd /Users/mmultra21/Documents/retro21_finance

# Activate virtual environment (already created)
source venv/bin/activate

# Install core dependencies (if not already done)
pip install fastapi uvicorn pydantic requests python-multipart
```

### Step 2: Start the Server
```bash
# Use the simple test server (no database needed)
python test_api_server.py
```

That's it! Open your browser to: **http://127.0.0.1:8000/docs**

---

## What You Can Do Now

### 1. **View API Documentation**
- Open: http://127.0.0.1:8000/docs
- Interactive interface to test all endpoints

### 2. **Check Server Health**
```bash
curl http://127.0.0.1:8000/health
```

### 3. **Get Narrative Templates**
```bash
curl http://127.0.0.1:8000/narrate/templates
```

### 4. **Generate Financial Narratives** (requires LLM server)
```bash
curl -X POST http://127.0.0.1:8000/narrate \
  -H "Content-Type: application/json" \
  -d '{
    "template": "Summarize these facts: {facts}",
    "facts": {
      "total_income": "$5000",
      "total_expenses": "$3200",
      "net_savings": "$1800"
    }
  }'
```

### 5. **List Available Forms**
```bash
curl http://127.0.0.1:8000/forms/available
```

---

## Adding LLM Features (Optional)

To enable AI-powered financial narratives:

### Option A: Use Mock LLM Server (Testing)
```bash
# Terminal 1 - Start mock LLM
source venv/bin/activate
python mock_hermes_server.py

# Terminal 2 - Start API (already running from above)
```

### Option B: Use Real Hermes LLM (Full Features)
```bash
# Terminal 1 - Start Hermes (requires llama.cpp installed)
./run_hermes3.sh

# Terminal 2 - Start API (already running from above)
```

---

## Running Tests

### Quick API Test
```bash
source venv/bin/activate
python test_api.py
```

### Comprehensive Financial Test
```bash
# Make sure API server is running first!
python test_financial_use_case.py
```

Expected output:
```
✅ PASS: Health Check
✅ PASS: Narrative Templates
✅ PASS: Forms Available
...
Pass Rate: 100.0%
```

---

## Alternative Startup Methods

### Method 1: Interactive Script
```bash
./simple_start.sh
# Then choose: 1 for test server, 2 for full app
```

### Method 2: Python Script
```bash
python run_server.py
# Automatically detects dependencies and starts appropriate server
```

### Method 3: Direct Python Command
```bash
# From project root
source venv/bin/activate
python test_api_server.py
```

---

## Troubleshooting

### Problem: "Module not found" error
**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install fastapi uvicorn pydantic requests
```

### Problem: "Port 8000 already in use"
**Solution:**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=8001 python test_api_server.py
```

### Problem: "ImportError: attempted relative import"
**Solution:**
```bash
# Use the test server instead of main.py directly
python test_api_server.py

# NOT this:
# python -m api.main  ❌
```

### Problem: LLM server not responding
**Solution:**
- LLM features are **optional** - the API works without it
- Use mock server for testing: `python mock_hermes_server.py`
- Check Hermes is running: `curl http://127.0.0.1:11434/health`

---

## Next Steps

### 1. Import Bank Transactions
Once you have CSV files from your bank:
```bash
curl -X POST "http://127.0.0.1:8000/ingest/csv" \
  -F "file=@transactions.csv" \
  -F "bank=chase"
```

### 2. Query Your Data
```bash
curl -X POST "http://127.0.0.1:8000/query/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "category": "Food"
  }'
```

### 3. Get Financial Analytics
```bash
curl "http://127.0.0.1:8000/analytics/summary?start_date=2024-01-01&end_date=2024-12-31"
```

### 4. Fill Tax Forms
```bash
curl -X POST "http://127.0.0.1:8000/forms/fill" \
  -H "Content-Type: application/json" \
  -d '{
    "form_type": "form_433a",
    "data": {
      "taxpayer": {"full_name": "John Doe"},
      "income": {"gross_monthly_wages": 5000}
    }
  }'
```

---

## Full Application Setup (Advanced)

If you want to use all features including database:

```bash
# 1. Install ALL dependencies (may take a while)
source venv/bin/activate
pip install -r personal-finance/requirements.txt

# Note: DuckDB may fail to compile on some systems
# If it fails, you can skip it for now

# 2. Start from project root with proper path
cd /Users/mmultra21/Documents/retro21_finance
export PYTHONPATH=/Users/mmultra21/Documents/retro21_finance:$PYTHONPATH

# 3. Start the server
python -c "
import sys
sys.path.insert(0, '.')
from personal_finance.api.main import app
import uvicorn
uvicorn.run(app, host='127.0.0.1', port=8000)
"
```

---

## Summary

**Recommended workflow for getting started:**

1. ✅ `source venv/bin/activate`
2. ✅ `python test_api_server.py`
3. ✅ Open http://127.0.0.1:8000/docs
4. ✅ Try the endpoints in the interactive docs!

**Need help?** Check the full documentation in [personal-finance/README.md](personal-finance/README.md)
