#!/bin/bash
# Monitor Raspberry Pi CPU temperature.
#
# Usage:
#   ./monitor_cpu_temp.sh              # single reading
#   ./monitor_cpu_temp.sh -c           # continuous monitoring
#   ./monitor_cpu_temp.sh -c -i 5      # every 5 seconds

set -euo pipefail

INTERVAL=1
CONTINUOUS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interval) INTERVAL="$2"; shift 2 ;;
        -c|--continuous) CONTINUOUS=true; shift ;;
        -h|--help)
            echo "Usage: $0 [-c] [-i seconds]"
            echo "  -c, --continuous  Continuous monitoring"
            echo "  -i, --interval    Polling interval in seconds (default: 1)"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

read_temp() {
    if [[ -f /sys/class/thermal/thermal_zone0/temp ]]; then
        echo "scale=2; $(cat /sys/class/thermal/thermal_zone0/temp)/1000" | bc
    elif command -v vcgencmd &>/dev/null; then
        vcgencmd measure_temp | cut -d'=' -f2 | cut -d"'" -f1
    else
        echo "N/A"
    fi
}

if [[ "$CONTINUOUS" == true ]]; then
    echo "Monitoring CPU temperature (Ctrl+C to stop)"
    echo "-------------------------------------------"
    while true; do
        printf "%s | CPU: %s°C\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$(read_temp)"
        sleep "$INTERVAL"
    done
else
    printf "%s | CPU: %s°C\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$(read_temp)"
fi
