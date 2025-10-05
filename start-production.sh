#!/bin/bash
#
# Personal Finance RAG System - Production Startup with Real Hermes-3
# Starts all required services with real LLM
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

# Configuration
LLAMA_SERVER="/Users/mmultra21/src/llama.cpp/build/bin/llama-server"
HERMES_MODEL="/Users/mmultra21/models/llama/hermes3-8b.Q4_K_M.gguf"
API_PORT=8000
HERMES_PORT=11434

# Log and PID directories
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

API_LOG="$LOG_DIR/api_server.log"
HERMES_LOG="$LOG_DIR/hermes_server.log"
API_PID="$PID_DIR/api_server.pid"
HERMES_PID="$PID_DIR/hermes_server.pid"

# Print functions
print_header() {
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${CYAN}Personal Finance RAG System - Production Startup${NC}           ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  ${YELLOW}with Real Hermes-3 LLM${NC}                                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# Check if port is in use
check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Kill process on port
kill_port() {
    local port=$1
    if check_port $port; then
        print_warning "Port $port in use. Cleaning up..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Check required files
check_requirements() {
    local missing=0

    if [ ! -f "$LLAMA_SERVER" ]; then
        print_error "llama-server not found at: $LLAMA_SERVER"
        missing=1
    else
        print_success "llama-server found"
    fi

    if [ ! -f "$HERMES_MODEL" ]; then
        print_error "Hermes model not found at: $HERMES_MODEL"
        missing=1
    else
        print_success "Hermes model found ($(ls -lh "$HERMES_MODEL" | awk '{print $5}'))"
    fi

    if [ ! -f "test_api_server.py" ]; then
        print_error "test_api_server.py not found"
        missing=1
    else
        print_success "API server found"
    fi

    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found"
        missing=1
    else
        print_success "Virtual environment found"
    fi

    if [ $missing -eq 1 ]; then
        exit 1
    fi
}

# Start Hermes-3 LLM server
start_hermes() {
    print_info "Starting Hermes-3 LLM Server on port $HERMES_PORT..."
    kill_port $HERMES_PORT

    # Start llama-server with Hermes-3
    nohup "$LLAMA_SERVER" \
        --model "$HERMES_MODEL" \
        --port $HERMES_PORT \
        --host 127.0.0.1 \
        --ctx-size 8192 \
        --n-predict 2048 \
        --threads 8 \
        --batch-size 512 \
        --n-gpu-layers 99 \
        --metrics \
        > "$HERMES_LOG" 2>&1 &

    local pid=$!
    echo $pid > "$HERMES_PID"

    # Wait for server to start
    local retries=0
    while [ $retries -lt 30 ]; do
        if check_port $HERMES_PORT; then
            print_success "Hermes-3 LLM Server started (PID: $pid)"
            print_info "Loading model... (this may take 10-30 seconds)"
            sleep 10  # Give time for model to load
            return 0
        fi
        sleep 2
        retries=$((retries + 1))
    done

    print_error "Hermes-3 LLM Server failed to start"
    print_info "Check logs: tail -f $HERMES_LOG"
    return 1
}

# Start API server
start_api() {
    print_info "Starting API Server on port $API_PORT..."
    kill_port $API_PORT

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

# Verify services
verify_services() {
    echo ""
    print_info "Verifying services..."
    sleep 2

    # Check Hermes health
    if curl -s http://127.0.0.1:$HERMES_PORT/health > /dev/null 2>&1; then
        local model_info=$(curl -s http://127.0.0.1:$HERMES_PORT/health 2>/dev/null || echo "{}")
        print_success "Hermes-3 LLM: http://127.0.0.1:$HERMES_PORT"
    else
        print_warning "Hermes-3 LLM may still be loading..."
    fi

    # Check API health
    if curl -s http://127.0.0.1:$API_PORT/health > /dev/null 2>&1; then
        print_success "API Server: http://127.0.0.1:$API_PORT"
    else
        print_error "API Server health check failed"
        return 1
    fi

    return 0
}

# Display final status
display_status() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${GREEN}✓ Production System Started Successfully${NC}                   ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}🚀 Services Running:${NC}"
    echo -e "  ${GREEN}•${NC} Hermes-3 LLM:      ${BLUE}http://127.0.0.1:$HERMES_PORT${NC}"
    echo -e "  ${GREEN}•${NC} Main Application:  ${BLUE}http://127.0.0.1:$API_PORT${NC}"
    echo -e "  ${GREEN}•${NC} API Documentation: ${BLUE}http://127.0.0.1:$API_PORT/docs${NC}"
    echo ""
    echo -e "${CYAN}📝 Log Files:${NC}"
    echo -e "  ${GREEN}•${NC} Hermes-3:    ${YELLOW}tail -f $HERMES_LOG${NC}"
    echo -e "  ${GREEN}•${NC} API Server:  ${YELLOW}tail -f $API_LOG${NC}"
    echo ""
    echo -e "${CYAN}🎯 Model Info:${NC}"
    echo -e "  ${GREEN}•${NC} Model:       Hermes-3-Llama-3.1-8B (Q4_K_M)"
    echo -e "  ${GREEN}•${NC} Context:     8192 tokens"
    echo -e "  ${GREEN}•${NC} GPU Layers:  99 (Metal acceleration)"
    echo ""
    echo -e "${CYAN}⚡ Quick Commands:${NC}"
    echo -e "  ${GREEN}•${NC} Stop:        ${YELLOW}./stop.sh${NC}"
    echo -e "  ${GREEN}•${NC} Status:      ${YELLOW}./status.sh${NC}"
    echo -e "  ${GREEN}•${NC} Test Query:  ${YELLOW}curl -X POST http://127.0.0.1:$HERMES_PORT/v1/chat/completions ...${NC}"
    echo ""
    echo -e "${GREEN}✨ Your Personal Finance RAG System with Real Hermes-3 is ready!${NC}"
    echo ""
}

# Main execution
main() {
    print_header
    check_requirements

    echo ""
    print_info "Starting production services..."
    echo ""

    if ! start_hermes; then
        print_error "Failed to start Hermes-3 server"
        print_info "Check logs: tail -f $HERMES_LOG"
        exit 1
    fi

    if ! start_api; then
        print_error "Failed to start API server"
        exit 1
    fi

    verify_services
    display_status
}

main
