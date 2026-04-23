#!/bin/bash
# Sync project files to Raspberry Pi and optionally start remote debugging.
#
# Configure via environment variables:
#   RPI_USER  — SSH username        (default: pi)
#   RPI_HOST  — hostname or IP      (default: raspberrypi.local)
#   REMOTE_DIR — target directory   (default: /home/$RPI_USER/Projects/ceramique)

set -euo pipefail

RPI_USER="${RPI_USER:-pi}"
RPI_HOST="${RPI_HOST:-raspberrypi.local}"
REMOTE_DIR="${REMOTE_DIR:-/home/$RPI_USER/Projects/ceramique}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing $LOCAL_DIR → $RPI_USER@$RPI_HOST:$REMOTE_DIR ..."
rsync -avz \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude '.venv' \
    "$LOCAL_DIR/" "$RPI_USER@$RPI_HOST:$REMOTE_DIR/"

echo "Installing dependencies on Raspberry Pi ..."
ssh "$RPI_USER@$RPI_HOST" "cd $REMOTE_DIR && \
    python3 -m venv venv && \
    source venv/bin/activate && \
    pip install --upgrade pip -q && \
    pip install -e '.[rpi]' -q"

if [[ "${1:-}" == "--debug" ]]; then
    echo "Starting remote debugger (debugpy) — connect VSCode to $RPI_HOST:5678"
    ssh "$RPI_USER@$RPI_HOST" "cd $REMOTE_DIR && \
        source venv/bin/activate && \
        python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m ceramique" &
else
    echo "Done. Run on RPi:  cd $REMOTE_DIR && source venv/bin/activate && sudo python -m ceramique"
fi
