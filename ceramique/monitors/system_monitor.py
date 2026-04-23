"""Raspberry Pi system health monitoring.

Reads CPU temperature, memory usage, and CPU load average on Linux.
Returns *None* for each metric on non-RPi platforms.
"""

import os
import platform
import subprocess
from typing import Any, Dict, Optional


class SystemMonitor:
    """Reads Raspberry Pi CPU temperature, memory, and load."""

    def __init__(self) -> None:
        self._is_linux = platform.system() == "Linux"

    @property
    def cpu_temperature(self) -> Optional[float]:
        """CPU temperature in °C, or *None* on non-RPi platforms."""
        if not self._is_linux:
            return None

        thermal_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(thermal_path):
            try:
                with open(thermal_path) as fh:
                    return int(fh.read().strip()) / 1000.0
            except (ValueError, OSError):
                pass

        try:
            output = subprocess.check_output(
                ["vcgencmd", "measure_temp"], timeout=2
            ).decode()
            return float(output.split("=")[1].split("'")[0])
        except (subprocess.SubprocessError, IndexError, ValueError):
            return None

    @property
    def memory(self) -> Optional[Dict[str, int]]:
        """Memory usage in kB: ``total``, ``free``, ``available``, ``used``."""
        if not self._is_linux:
            return None

        try:
            info: Dict[str, int] = {}
            with open("/proc/meminfo") as fh:
                for line in fh:
                    if ":" not in line:
                        continue
                    key, val = line.split(":", 1)
                    digits = "".join(c for c in val if c.isdigit())
                    if digits:
                        info[key.strip()] = int(digits)

            total = info.get("MemTotal", 0)
            available = info.get("MemAvailable", 0)
            return {
                "total": total,
                "free": info.get("MemFree", 0),
                "available": available,
                "used": total - available,
            }
        except OSError:
            return None

    @property
    def cpu_load(self) -> Optional[float]:
        """1-minute load average as a percentage (approximate)."""
        try:
            return os.getloadavg()[0] * 100
        except OSError:
            return None
