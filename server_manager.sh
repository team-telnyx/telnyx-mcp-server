#!/bin/bash

# Server Manager for Telnyx MCP Server
# Usage: ./server_manager.sh {start|stop|restart|status|logs}

# Configuration
SERVER_MODULE="src.telnyx_mcp_server.remote.server"
HOST="0.0.0.0"
PORT="8000"
LOG_FILE="server.log"
PID_FILE="server.pid"
PYTHON_CMD="python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is not running
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to check server health
is_healthy() {
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/health" 2>/dev/null | grep -q "200"; then
        return 0
    fi
    return 1
}

# Function to get server status
status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ Server process is running${NC} (PID: $PID)"
        
        # Check health endpoint
        if is_healthy; then
            echo -e "${GREEN}✓ Server is healthy${NC}"
            
            # Get detailed health info
            HEALTH_INFO=$(curl -s "http://localhost:$PORT/health" 2>/dev/null)
            if [ $? -eq 0 ]; then
                echo -e "  Status: $(echo $HEALTH_INFO | jq -r .status 2>/dev/null || echo "unknown")"
                echo -e "  Version: $(echo $HEALTH_INFO | jq -r .version 2>/dev/null || echo "unknown")"
                echo -e "  Protocol: $(echo $HEALTH_INFO | jq -r .protocol_version 2>/dev/null || echo "unknown")"
            fi
        else
            echo -e "${YELLOW}⚠ Server process is running but not responding to health checks${NC}"
        fi
        
        echo -e "  URL: http://localhost:$PORT"
        echo -e "  Module: $SERVER_MODULE"
        echo -e "  Log file: $LOG_FILE"
    else
        echo -e "${RED}✗ Server is not running${NC}"
    fi
}

# Function to start the server
start() {
    if is_running; then
        echo -e "${YELLOW}Server is already running${NC}"
        status
        return 1
    fi
    
    echo -e "${GREEN}Starting Telnyx MCP Server...${NC}"
    
    # Clear old log file
    > "$LOG_FILE"
    
    # Start the server in the background
    nohup $PYTHON_CMD -m "$SERVER_MODULE" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    # Wait for server to be ready
    echo -n "Waiting for server to be ready"
    for i in {1..10}; do
        echo -n "."
        sleep 1
        if is_healthy; then
            echo ""
            echo -e "${GREEN}✓ Server started successfully${NC}"
            status
            echo ""
            echo "To view logs: tail -f $LOG_FILE"
            return 0
        fi
    done
    
    echo ""
    if is_running; then
        echo -e "${YELLOW}⚠ Server process started but health check failed${NC}"
        echo "The server may still be initializing. Check logs for details."
    else
        echo -e "${RED}✗ Failed to start server${NC}"
        rm -f "$PID_FILE"
    fi
    
    echo "Recent log entries:"
    tail -n 20 "$LOG_FILE"
    return 1
}

# Function to stop the server
stop() {
    if ! is_running; then
        echo -e "${YELLOW}Server is not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping server (PID: $PID)...${NC}"
    
    # Try graceful shutdown first
    kill "$PID" 2>/dev/null
    
    # Wait up to 5 seconds for graceful shutdown
    for i in {1..5}; do
        if ! is_running; then
            echo -e "${GREEN}✓ Server stopped gracefully${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo -e "${YELLOW}Force stopping server...${NC}"
    kill -9 "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    
    echo -e "${GREEN}✓ Server stopped${NC}"
}

# Function to restart the server
restart() {
    echo -e "${YELLOW}Restarting server...${NC}"
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
    
    echo -e "${GREEN}Showing last 50 lines of $LOG_FILE${NC}"
    echo "----------------------------------------"
    tail -n 50 "$LOG_FILE"
    echo "----------------------------------------"
    echo ""
    echo "To follow logs in real-time: tail -f $LOG_FILE"
}

# Function to clean up any stray processes
cleanup() {
    echo -e "${YELLOW}Cleaning up any stray server processes...${NC}"
    
    # Find and kill any processes running our server module
    pgrep -f "$SERVER_MODULE" | while read pid; do
        echo "  Killing process $pid"
        kill -9 "$pid" 2>/dev/null
    done
    
    # Also check for uvicorn processes on our port
    lsof -ti:$PORT | while read pid; do
        echo "  Killing process $pid using port $PORT"
        kill -9 "$pid" 2>/dev/null
    done
    
    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ Cleanup complete${NC}"
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
    cleanup)
        cleanup
        ;;
    *)
        echo "Telnyx MCP Server Manager"
        echo "Usage: $0 {start|stop|restart|status|logs|cleanup}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the server"
        echo "  stop     - Stop the server"
        echo "  restart  - Restart the server"
        echo "  status   - Show server status"
        echo "  logs     - Show recent log entries"
        echo "  cleanup  - Kill all server processes (use with caution)"
        echo ""
        exit 1
        ;;
esac

exit 0