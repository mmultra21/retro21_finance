#!/bin/bash
#
# Personal Finance RAG System - Stop Script
# Gracefully stops all application services
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

API_PID="$PID_DIR/api_server.pid"
HERMES_PID="$PID_DIR/hermes_server.pid"

# Port configuration
API_PORT=8000
HERMES_PORT=11434

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${CYAN}Personal Finance RAG System - Shutdown${NC}                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to stop service by PID file
stop_service() {
    local pid_file=$1
    local service_name=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            print_info "Stopping $service_name (PID: $pid)..."
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null
            sleep 1

            if ps -p $pid > /dev/null 2>&1; then
                print_warning "$service_name did not stop gracefully, forcing..."
                kill -9 $pid 2>/dev/null
            fi

            print_success "$service_name stopped"
        else
            print_info "$service_name not running (stale PID file)"
        fi
        rm -f "$pid_file"
    else
        print_info "$service_name PID file not found"
    fi
}

# Function to stop service by port
stop_port() {
    local port=$1
    local service_name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_info "Stopping processes on port $port ($service_name)..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        print_success "Port $port freed"
    fi
}

# Function to cleanup background processes
cleanup_processes() {
    print_info "Cleaning up background Python processes..."

    # Kill any remaining test_api_server.py processes
    pkill -9 -f "test_api_server.py" 2>/dev/null || true

    # Kill any remaining mock_hermes_server.py processes
    pkill -9 -f "mock_hermes_server.py" 2>/dev/null || true

    sleep 1
    print_success "Background processes cleaned up"
}

# Main execution
main() {
    print_header

    # Stop services by PID files
    stop_service "$API_PID" "API Server"
    stop_service "$HERMES_PID" "Hermes LLM Server"

    echo ""

    # Stop by port as fallback
    stop_port $API_PORT "API Server"
    stop_port $HERMES_PORT "Hermes LLM"

    echo ""

    # Cleanup any remaining processes
    cleanup_processes

    echo ""
    echo -e "${GREEN}✓ All services stopped successfully${NC}"
    echo ""
}

# Run main function
main
