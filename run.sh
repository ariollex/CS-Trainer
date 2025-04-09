#!/bin/bash

cd "$(dirname "$0")"

PID=$(pgrep -f "uvicorn main:app")
if [ -n "$PID" ]; then
    echo "Detected running uvicorn server (PID: $PID). Terminating it..."
    kill "$PID"
    sleep 2
    PID=$(pgrep -f "uvicorn main:app")
    if [ -n "$PID" ]; then
        echo "Server did not terminate cleanly, forcing shutdown..."
        kill -9 "$PID"
    fi
fi

echo "Starting uvicorn server"
# Launching uvicorn server, assuming there is an 'app' object in main.py
uvicorn main:app --host 0.0.0.0 --port 8000
