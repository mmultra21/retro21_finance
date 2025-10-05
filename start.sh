#!/bin/bash
#
# Personal Finance RAG System - Startup Script
# Starts all required services: API Server, Hermes LLM, and Web UI
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

# Log file location
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

API_LOG="$LOG_DIR/api_server.log"
HERMES_LOG="$LOG_DIR/hermes_server.log"

# PID file location
PID_DIR="$SCRIPT_DIR/pids"
mkdir -p "$PID_DIR"

API_PID="$PID_DIR/api_server.pid"
HERMES_PID="$PID_DIR/hermes_server.pid"

# Port configuration
API_PORT=8000
HERMES_PORT=11434

# Function to print colored messages
print_header() {
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${CYAN}Personal Finance RAG System - Startup${NC}                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

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

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local process_name=$2

    if check_port $port; then
        print_warning "Port $port is already in use. Cleaning up..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2

        if check_port $port; then
            print_error "Failed to free port $port"
            return 1
        else
            print_success "Freed port $port"
        fi
    fi
    return 0
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found at: $SCRIPT_DIR/venv"
        print_info "Please create it with: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    print_success "Virtual environment found"
}

# Function to check required files
check_files() {
    local missing=0

    if [ ! -f "test_api_server.py" ]; then
        print_error "test_api_server.py not found"
        missing=1
    fi

    if [ ! -f "mock_hermes_server.py" ]; then
        print_error "mock_hermes_server.py not found"
        missing=1
    fi

    if [ ! -f ".env" ]; then
        print_warning ".env file not found - creating default"
        cat > .env << 'EOF'
# SerpAPI Configuration
SERPAPI_KEY=your_serpapi_key_here

# Hermes LLM Configuration
HERMES_URL=http://127.0.0.1:11434
EOF
    fi

    if [ $missing -eq 1 ]; then
        print_error "Required files are missing"
        exit 1
    fi

    print_success "All required files present"
}

# Function to start Hermes server
start_hermes() {
    print_info "Starting Hermes LLM Server on port $HERMES_PORT..."

    if ! kill_port $HERMES_PORT "Hermes"; then
        return 1
    fi

    # Start Hermes3 LLM server in background
    nohup /Users/mmultra21/src/llama.cpp/build/bin/llama-server \
        -m /Users/mmultra21/models/llama/hermes3-8b.Q4_K_M.gguf \
        --port 11434 \
        --ctx-size 8192 \
        --n-predict 512 > "$HERMES_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$HERMES_PID"

    # Wait for server to start
    local retries=0
    while [ $retries -lt 10 ]; do
        if check_port $HERMES_PORT; then
            print_success "Hermes LLM Server started (PID: $pid)"
            return 0
        fi
        sleep 1
        retries=$((retries + 1))
    done

    print_error "Hermes LLM Server failed to start"
    return 1
}

# Function to start API server
start_api() {
    print_info "Starting API Server on port $API_PORT..."

    if ! kill_port $API_PORT "API Server"; then
        return 1
    fi

    # Start API server in background
    source venv/bin/activate
    nohup python test_api_server.py > "$API_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$API_PID"

    # Wait for server to start
    local retries=0
    while [ $retries -lt 10 ]; do
        if check_port $API_PORT; then
            print_success "API Server started (PID: $pid)"
            return 0
        fi
        sleep 1
        retries=$((retries + 1))
    done

    print_error "API Server failed to start"
    return 1
}

# Function to verify services
verify_services() {
    echo ""
    print_info "Verifying services..."

    local all_ok=1

    # Check Hermes health
    if curl -s http://127.0.0.1:$HERMES_PORT/health > /dev/null 2>&1; then
        print_success "Hermes LLM: http://127.0.0.1:$HERMES_PORT"
    else
        print_error "Hermes LLM health check failed"
        all_ok=0
    fi

    # Check API health
    if curl -s http://127.0.0.1:$API_PORT/health > /dev/null 2>&1; then
        print_success "API Server: http://127.0.0.1:$API_PORT"
    else
        print_error "API Server health check failed"
        all_ok=0
    fi

    return $all_ok
}

# Function to display final status
display_status() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${GREEN}✓ All Services Started Successfully${NC}                        ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}📊 Service URLs:${NC}"
    echo -e "  ${GREEN}•${NC} Main Application:  ${BLUE}http://127.0.0.1:$API_PORT${NC}"
    echo -e "  ${GREEN}•${NC} API Documentation: ${BLUE}http://127.0.0.1:$API_PORT/docs${NC}"
    echo -e "  ${GREEN}•${NC} Hermes LLM:        ${BLUE}http://127.0.0.1:$HERMES_PORT${NC}"
    echo ""
    echo -e "${CYAN}📝 Log Files:${NC}"
    echo -e "  ${GREEN}•${NC} API Server:  ${YELLOW}$API_LOG${NC}"
    echo -e "  ${GREEN}•${NC} Hermes LLM:  ${YELLOW}$HERMES_LOG${NC}"
    echo ""
    echo -e "${CYAN}🎯 Quick Commands:${NC}"
    echo -e "  ${GREEN}•${NC} Stop services:   ${YELLOW}./stop.sh${NC}"
    echo -e "  ${GREEN}•${NC} Check status:    ${YELLOW}./status.sh${NC}"
    echo -e "  ${GREEN}•${NC} View API logs:   ${YELLOW}tail -f $API_LOG${NC}"
    echo -e "  ${GREEN}•${NC} View Hermes logs: ${YELLOW}tail -f $HERMES_LOG${NC}"
    echo ""
    echo -e "${GREEN}✨ Your Personal Finance RAG System is ready!${NC}"
    echo ""
}

# Main execution
main() {
    print_header

    # Pre-flight checks
    check_venv
    check_files

    echo ""
    print_info "Starting services..."
    echo ""

    # Start services
    if ! start_hermes; then
        print_error "Failed to start Hermes server"
        exit 1
    fi

    if ! start_api; then
        print_error "Failed to start API server"
        exit 1
    fi

    # Verify all services
    if ! verify_services; then
        print_error "Service verification failed"
        exit 1
    fi

    # Display success message
    display_status
}

# Run main function
main
