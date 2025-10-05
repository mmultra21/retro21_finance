#!/bin/bash
# Simple startup script for the Personal Finance API

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if we're in the right directory
if [ ! -f "test_api_server.py" ]; then
    echo "❌ Please run this script from the retro21_finance directory"
    exit 1
fi

echo "🚀 Starting Personal Finance API..."
echo ""
echo "Choose startup mode:"
echo "  1) Simple test server (no database - recommended for testing)"
echo "  2) Full application (requires all dependencies)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "Starting simplified test server..."
        python test_api_server.py
        ;;
    2)
        echo ""
        echo "Starting full application..."
        cd personal-finance
        python3 -c "
import sys
sys.path.insert(0, '..')
from api.main import app
import uvicorn
print('Starting full Personal Finance API on http://127.0.0.1:8000')
uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
"
        ;;
    *)
        echo "Invalid choice. Using test server..."
        python test_api_server.py
        ;;
esac
