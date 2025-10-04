#!/usr/bin/env bash
# Production startup script for Personal Finance API + Frontend

set -euo pipefail

# Configuration
export ENVIRONMENT=production
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"
export LOG_LEVEL="${LOG_LEVEL:-info}"

# Check if frontend is built
FRONTEND_DIST="frontend/dist"
if [[ ! -d "$FRONTEND_DIST" ]]; then
    echo "❌ Frontend not built. Building now..."
    if [[ -d "frontend" ]]; then
        cd frontend
        npm install
        npm run build
        cd ..
        echo "✅ Frontend built successfully"
    else
        echo "⚠️  Frontend directory not found. API will run in API-only mode."
    fi
fi

# Start the server
echo "🚀 Starting Personal Finance API in production mode..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Frontend: $([ -d "$FRONTEND_DIST" ] && echo "✅ Available" || echo "❌ Not available")"
echo "   Hermes LLM: ${HERMES_URL:-http://127.0.0.1:11434}"

cd personal-finance
python -m api.main