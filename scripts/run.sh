#!/bin/bash
# Run the kiln controller with root privileges (required for GPIO access).
set -euo pipefail
cd "$(dirname "$0")/.."
sudo -E python3 -m ceramique
