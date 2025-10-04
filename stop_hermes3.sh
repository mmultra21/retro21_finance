#!/usr/bin/env bash
# Stop the Hermes3 LLM server

PID_FILE="${PID_FILE:-/tmp/llm_server.pid}"

if [[ ! -f "$PID_FILE" ]]; then
    echo "❌ PID file not found: $PID_FILE"
    echo "Server may not be running or was started differently."
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo "❌ Process $PID is not running"
    rm -f "$PID_FILE"
    exit 1
fi

echo "🛑 Stopping Hermes3 server (PID: $PID)..."
kill "$PID"

# Wait for graceful shutdown
for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "✅ Server stopped successfully"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if graceful shutdown failed
echo "⚡ Force stopping server..."
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "✅ Server force stopped"