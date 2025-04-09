#!/bin/bash

set -e

cd "${DEPLOY_PATH}"

echo "Updating code from Git repository..."
git fetch --all
if ! git pull origin main; then
    echo "Warning: Git pull failed! Forcing code reset..."
    git reset --hard origin/main
    git clean -fd
    git pull origin main
fi

VENV_DIR="${DEPLOY_PATH}/venv"
PID_FILE="${DEPLOY_PATH}/server.pid"
LOG_FILE="${DEPLOY_PATH}/server.log"

if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo "Virtual environment created at ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found!"
    exit 1
fi

stop_server() {
    if [ -f "${PID_FILE}" ]; then
        local pid=$(cat "${PID_FILE}")
        echo "Stopping running server (PID: $pid)..."
        kill "$pid" || true
        sleep 2
        if ps -p "$pid" > /dev/null; then
            echo "Force killing server (PID: $pid)..."
            kill -9 "$pid"
        fi
        rm -f "${PID_FILE}"
    else
        local pid=$(pgrep -f "uvicorn main:app")
        if [ -n "$pid" ]; then
            echo "Found orphaned server process (PID: $pid). Stopping it..."
            kill "$pid"
        fi
    fi
}

stop_server

echo "Starting Uvicorn server..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "${LOG_FILE}" 2>&1 &
echo $! > "${PID_FILE}"

sleep 3
if ! ps -p $(cat "${PID_FILE}") > /dev/null; then
    echo "Error: Server failed to start!"
    echo "Check log file: ${LOG_FILE}"
    exit 1
fi

echo "Server started successfully (PID: $(cat "${PID_FILE}"))"
echo "Logs are being written to: ${LOG_FILE}"
echo "Deployment completed successfully"