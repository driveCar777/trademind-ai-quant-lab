#!/bin/bash
# TradeMind Factor Worker - Auto-start daemon
# Xavier-02 (192.168.1.201) - Port 8001

WORKER_DIR="/home/dji/factor-worker-v1"
PID_FILE="/tmp/factor-worker.pid"
LOG_FILE="/tmp/factor-worker.log"

stop_worker() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Stopping factor-worker (PID=$PID)..."
            kill "$PID"
            sleep 1
        fi
        rm -f "$PID_FILE"
    fi
    # Also kill any stray processes
    pkill -f "server.py" 2>/dev/null
    fuser -k 8001/tcp 2>/dev/null
    echo "Stopped"
}

start_worker() {
    cd "$WORKER_DIR" || exit 1
    setsid python3 server.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Started factor-worker (PID=$(cat $PID_FILE))"
}

status_worker() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "factor-worker is RUNNING (PID=$PID)"
            curl -s http://127.0.0.1:8001/health 2>/dev/null || echo "  (health check failed)"
        else
            echo "factor-worker is DEAD (stale PID file)"
        fi
    else
        echo "factor-worker is STOPPED (no PID file)"
    fi
}

case "$1" in
    start)
        stop_worker 2>/dev/null
        start_worker
        ;;
    stop)
        stop_worker
        ;;
    restart)
        stop_worker 2>/dev/null
        sleep 1
        start_worker
        ;;
    status)
        status_worker
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
