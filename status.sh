#!/bin/bash
#
# Personal Finance RAG System - Status Script
# Displays current status of all services
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# PID file location
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"

API_PID="$PID_DIR/api_server.pid"
HERMES_PID="$PID_DIR/hermes_server.pid"

# Port configuration
API_PORT=8000
HERMES_PORT=11434

# Function to print colored messages
print_header() {
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${CYAN}Personal Finance RAG System - Status${NC}                       ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to check service status
check_service() {
    local pid_file=$1
    local service_name=$2
    local port=$3
    local url=$4

    echo -e "${CYAN}$service_name:${NC}"

    # Check PID file
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "  Status:  ${GREEN}● Running${NC}"
            echo -e "  PID:     ${YELLOW}$pid${NC}"
        else
            echo -e "  Status:  ${RED}● Stopped${NC} (stale PID file)"
            echo -e "  PID:     ${RED}$pid (dead)${NC}"
        fi
    else
        echo -e "  Status:  ${RED}● Stopped${NC}"
        echo -e "  PID:     ${RED}N/A${NC}"
    fi

    # Check port
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  Port:    ${GREEN}$port (in use)${NC}"
    else
        echo -e "  Port:    ${RED}$port (free)${NC}"
    fi

    # Check health endpoint
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "  Health:  ${GREEN}✓ OK${NC}"
        echo -e "  URL:     ${BLUE}$url${NC}"
    else
        echo -e "  Health:  ${RED}✗ Not responding${NC}"
        echo -e "  URL:     ${RED}$url${NC}"
    fi

    echo ""
}

# Function to check Qdrant database
check_qdrant() {
    echo -e "${CYAN}Qdrant Vector Database:${NC}"

    if [ -d "data/qdrant_db" ]; then
        local size=$(du -sh data/qdrant_db 2>/dev/null | cut -f1)
        echo -e "  Status:  ${GREEN}● Initialized${NC}"
        echo -e "  Path:    ${YELLOW}data/qdrant_db${NC}"
        echo -e "  Size:    ${YELLOW}$size${NC}"

        # Try to get document count via API
        if curl -s http://127.0.0.1:$API_PORT/documents > /dev/null 2>&1; then
            local count=$(curl -s http://127.0.0.1:$API_PORT/documents | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('count', 0))" 2>/dev/null || echo "N/A")
            echo -e "  Documents: ${YELLOW}$count${NC}"
        fi
    else
        echo -e "  Status:  ${RED}● Not initialized${NC}"
        echo -e "  Path:    ${RED}data/qdrant_db (missing)${NC}"
    fi

    echo ""
}

# Function to check logs
check_logs() {
    echo -e "${CYAN}Recent Activity (Last 5 lines):${NC}"
    echo ""

    if [ -f "$LOG_DIR/api_server.log" ]; then
        echo -e "${YELLOW}API Server Log:${NC}"
        tail -5 "$LOG_DIR/api_server.log" 2>/dev/null | sed 's/^/  /'
        echo ""
    fi

    if [ -f "$LOG_DIR/hermes_server.log" ]; then
        echo -e "${YELLOW}Hermes Server Log:${NC}"
        tail -5 "$LOG_DIR/hermes_server.log" 2>/dev/null | sed 's/^/  /'
        echo ""
    fi
}

# Function to show quick actions
show_actions() {
    echo -e "${CYAN}Quick Actions:${NC}"
    echo -e "  ${GREEN}•${NC} Start services:    ${YELLOW}./start.sh${NC}"
    echo -e "  ${GREEN}•${NC} Stop services:     ${YELLOW}./stop.sh${NC}"
    echo -e "  ${GREEN}•${NC} Restart services:  ${YELLOW}./stop.sh && ./start.sh${NC}"
    echo -e "  ${GREEN}•${NC} View API logs:     ${YELLOW}tail -f logs/api_server.log${NC}"
    echo -e "  ${GREEN}•${NC} View Hermes logs:  ${YELLOW}tail -f logs/hermes_server.log${NC}"
    echo ""
}

# Main execution
main() {
    print_header

    # Check services
    check_service "$HERMES_PID" "Hermes LLM Server" "$HERMES_PORT" "http://127.0.0.1:$HERMES_PORT/health"
    check_service "$API_PID" "API Server" "$API_PORT" "http://127.0.0.1:$API_PORT/health"

    # Check Qdrant
    check_qdrant

    # Show logs
    if [ -d "$LOG_DIR" ] && [ "$(ls -A $LOG_DIR 2>/dev/null)" ]; then
        check_logs
    fi

    # Show actions
    show_actions
}

# Run main function
main
