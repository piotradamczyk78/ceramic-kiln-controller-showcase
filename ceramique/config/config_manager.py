"""Hardware configuration loader for the kiln controller.

Reads a YAML configuration file and exposes typed accessors for
GPIO pins, power parameters, sensor settings, and PID tuning.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """Loads and provides typed access to hardware configuration."""

    DEFAULT_CONFIG = "config/hardware_config.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML config file. When *None*,
                the default ``config/hardware_config.yaml`` relative to
                the package root is used.
        """
        if config_path is None:
            package_root = Path(__file__).resolve().parent.parent
            config_path = str(package_root / self.DEFAULT_CONFIG)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as fh:
            self._config: Dict[str, Any] = yaml.safe_load(fh)

    # -- Section accessors ---------------------------------------------------

    def get_gpio_config(self) -> Dict[str, Any]:
        """Return the full GPIO pin mapping."""
        return self._config.get("gpio", {})

    def get_power_config(self) -> Dict[str, Any]:
        """Return AC mains power parameters."""
        return self._config.get("power", {})

    def get_sensor_config(self, sensor_name: str) -> Optional[Dict[str, Any]]:
        """Return configuration for a specific sensor.

        Args:
            sensor_name: One of ``hx711``, ``max31855``, ``sht31``, ``pzem``.
        """
        return self._config.get("sensors", {}).get(sensor_name)

    def get_pid_config(self) -> Dict[str, Any]:
        """Return PID controller tuning parameters."""
        return self._config.get("pid", {})

    # -- Convenience properties ----------------------------------------------

    @property
    def zero_cross_pin(self) -> int:
        """GPIO pin for AC zero-cross detection."""
        return self._config["gpio"]["zero_cross_pin"]

    @property
    def triac_pin(self) -> int:
        """GPIO pin for TRIAC gate control."""
        return self._config["gpio"]["triac_pin"]

    @property
    def frequency(self) -> int:
        """AC mains frequency in Hz."""
        return self._config["power"]["frequency_hz"]

    @property
    def half_cycle_time(self) -> float:
        """Duration of one AC half-cycle in seconds."""
        return self._config["power"]["half_cycle_time"]
