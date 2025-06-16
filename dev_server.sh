#!/bin/bash

# Development Server Manager for Telnyx MCP Server
# Usage: ./dev_server.sh {start|stop|restart|status|logs}

# Configuration
APP_MODULE="src.telnyx_mcp_server.remote.server:app"
HOST="0.0.0.0"
PORT="8000"
LOG_FILE="server_dev.log"
PID_FILE="server_dev.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to check server health
is_healthy() {
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/health" 2>/dev/null)
    if [ "$RESPONSE" = "200" ]; then
        return 0
    fi
    return 1
}

# Function to get server status
status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ Development server process is running${NC} (PID: $PID)"
        
        # Check health endpoint
        if is_healthy; then
            echo -e "${GREEN}✓ Server is healthy and responding${NC}"
            
            # Get health details
            HEALTH_JSON=$(curl -s "http://localhost:$PORT/health" 2>/dev/null)
            if [ $? -eq 0 ] && command -v jq &> /dev/null; then
                STATUS=$(echo "$HEALTH_JSON" | jq -r .status 2>/dev/null)
                VERSION=$(echo "$HEALTH_JSON" | jq -r .version 2>/dev/null)
                PROTOCOL=$(echo "$HEALTH_JSON" | jq -r .protocol_version 2>/dev/null)
                [ "$STATUS" != "null" ] && echo -e "  Health Status: $STATUS"
                [ "$VERSION" != "null" ] && echo -e "  Version: $VERSION"
                [ "$PROTOCOL" != "null" ] && echo -e "  Protocol: $PROTOCOL"
            fi
        else
            echo -e "${YELLOW}⚠ Server process running but not responding to health checks${NC}"
        fi
        
        echo -e "  URL: http://localhost:$PORT"
        echo -e "  API Docs: http://localhost:$PORT/docs"
        echo -e "  OAuth Test: http://localhost:$PORT/test-auth"
        echo -e "  Features: Hot reload enabled"
        echo -e "  Log file: $LOG_FILE"
    else
        echo -e "${RED}✗ Development server is not running${NC}"
    fi
}

# Function to start the server
start() {
    if is_running; then
        echo -e "${YELLOW}Development server is already running${NC}"
        status
        return 1
    fi
    
    echo -e "${GREEN}Starting Telnyx MCP Development Server...${NC}"
    echo -e "${BLUE}Features:${NC}"
    echo "  • Hot reload enabled (changes detected automatically)"
    echo "  • Detailed error messages"
    echo "  • Request logging"
    echo ""
    
    # Clear old log file
    > "$LOG_FILE"
    
    # Start uvicorn with hot reload
    nohup python -m uvicorn "$APP_MODULE" \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dir src \
        --log-level info \
        > "$LOG_FILE" 2>&1 &
    
    PID=$!
    echo $PID > "$PID_FILE"
    
    # Wait for server to be healthy
    echo -n "Waiting for server to be ready"
    READY=false
    for i in {1..15}; do
        echo -n "."
        sleep 1
        if is_healthy; then
            READY=true
            break
        fi
    done
    echo ""
    
    if [ "$READY" = true ]; then
        echo -e "${GREEN}✓ Development server started successfully${NC}"
        echo ""
        status
        echo ""
        echo -e "${BLUE}Quick commands:${NC}"
        echo "  View logs:   tail -f $LOG_FILE"
        echo "  Test OAuth:  open http://localhost:$PORT/test-auth"
        echo "  API docs:    open http://localhost:$PORT/docs"
        echo ""
        echo -e "${YELLOW}Hot reload is enabled - server will restart automatically on code changes${NC}"
    else
        if is_running; then
            echo -e "${YELLOW}⚠ Server process started but health check failed${NC}"
            echo "The server may still be initializing. Recent logs:"
        else
            echo -e "${RED}✗ Failed to start development server${NC}"
            echo "Recent logs:"
            rm -f "$PID_FILE"
        fi
        tail -n 30 "$LOG_FILE"
        return 1
    fi
}

# Function to stop the server
stop() {
    if ! is_running; then
        echo -e "${YELLOW}Development server is not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping development server (PID: $PID)...${NC}"
    
    # Kill the main process and all children
    pkill -P "$PID" 2>/dev/null
    kill "$PID" 2>/dev/null
    
    # Wait for shutdown
    for i in {1..5}; do
        if ! is_running; then
            echo -e "${GREEN}✓ Development server stopped${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo -e "${YELLOW}Force stopping server...${NC}"
    kill -9 "$PID" 2>/dev/null
    pkill -9 -P "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    
    echo -e "${GREEN}✓ Development server stopped${NC}"
}

# Function to restart the server
restart() {
    echo -e "${YELLOW}Restarting development server...${NC}"
    stop
    sleep 1
    start
}

# Function to show logs
logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}No log file found${NC}"
        return 1
    fi
    
    # Follow logs with color highlighting
    echo -e "${GREEN}Following $LOG_FILE (Ctrl+C to stop)${NC}"
    echo "----------------------------------------"
    tail -f "$LOG_FILE" | sed \
        -e 's/ERROR/\x1b[31mERROR\x1b[0m/g' \
        -e 's/WARNING/\x1b[33mWARNING\x1b[0m/g' \
        -e 's/INFO/\x1b[32mINFO\x1b[0m/g' \
        -e 's/DEBUG/\x1b[34mDEBUG\x1b[0m/g'
}

# Function to show recent errors
errors() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}No log file found${NC}"
        return 1
    fi
    
    echo -e "${RED}Recent errors from $LOG_FILE${NC}"
    echo "----------------------------------------"
    grep -i "error\|exception\|traceback" "$LOG_FILE" | tail -n 20
    echo "----------------------------------------"
}

# Main script logic
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    errors)
        errors
        ;;
    *)
        echo "Telnyx MCP Development Server Manager"
        echo "Usage: $0 {start|stop|restart|status|logs|errors}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the development server with hot reload"
        echo "  stop     - Stop the development server"
        echo "  restart  - Restart the development server"
        echo "  status   - Show server status"
        echo "  logs     - Follow server logs with color highlighting"
        echo "  errors   - Show recent errors from logs"
        echo ""
        echo "Features:"
        echo "  • Hot reload - automatically restarts on code changes"
        echo "  • Detailed logging and error messages"
        echo "  • Color-coded log output"
        echo ""
        exit 1
        ;;
esac

exit 0