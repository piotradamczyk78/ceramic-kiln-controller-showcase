"""Main application controller — connects all kiln subsystems.

Orchestrates the sensor polling thread, PID control loop, TRIAC power
output, GUI updates, data logging, and firing profile execution.

Control loop (runs every 100 ms in a background thread)::

    1. Read thermocouple temperature from SensorManager
    2. Look up expected temperature from the firing profile
    3. Feed both into the PID controller → output (0–500 ms)
    4. Convert PID output to TRIAC on/off delays
    5. Update GUI with latest readings
"""

import logging
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional

from ceramique.config.config_manager import ConfigManager
from ceramique.controllers.pid_controller import PIDController
from ceramique.controllers.sensor_manager import SensorManager
from ceramique.controllers.triac_controller import TriacController
from ceramique.core.event_dispatcher import EventDispatcher
from ceramique.logging.data_logger import DataLogger
from ceramique.profiles.profile_manager import ProfileManager
from ceramique.profiles.temperature_curves import TemperatureCurves
from ceramique.ui.kiln_gui import KilnGUI
from ceramique.ui.temperature_plot import TemperaturePlot

log = logging.getLogger(__name__)


class KilnController:
    """Top-level coordinator for the ceramic kiln."""

    CONTROL_INTERVAL = 0.1  # seconds between PID updates

    def __init__(self) -> None:
        self._config = ConfigManager()
        self._dispatcher = EventDispatcher()

        self._triac = TriacController(
            self._dispatcher,
            self._config.get_gpio_config(),
            self._config.get_power_config(),
        )

        sensor_cfg = {
            "gpio": self._config.get_gpio_config(),
            "hx711": self._config.get_sensor_config("hx711") or {},
            "max31855": self._config.get_sensor_config("max31855") or {},
            "sht31": self._config.get_sensor_config("sht31") or {},
            "pzem": self._config.get_sensor_config("pzem") or {},
        }
        self._sensors = SensorManager(self._dispatcher, sensor_cfg)
        self._logger = DataLogger()
        self._profile_mgr = ProfileManager()

        # PID — instantiated ONCE, called repeatedly (fixes the stateless bug)
        pid_cfg = self._config.get_pid_config()
        self._pid = PIDController(
            kp=pid_cfg.get("kp", 320),
            ki=pid_cfg.get("ki", 160),
            kd=pid_cfg.get("kd", 8),
            output_limits=(
                pid_cfg.get("output_min", 0),
                pid_cfg.get("output_max", 500),
            ),
        )

        self._half_cycle_ms = self._config.half_cycle_time * 1000

        # Firing state
        self._curves: Optional[TemperatureCurves] = None
        self._start_time: Optional[datetime] = None
        self._running = False

        # GUI
        self._gui = KilnGUI(
            profile_names=self._profile_mgr.names,
            on_profile_change=self._on_profile_change,
            on_ir_temp_set=self._on_ir_temp_set,
            on_finish=self.stop,
        )

        self._dispatcher.register("sensor_readings", self._on_sensor_readings)

    # -- Event handlers -------------------------------------------------------

    def _on_profile_change(self, name: str) -> None:
        """Handle firing profile selection from the GUI."""
        profile = self._profile_mgr.get_profile(name)
        if profile is None:
            return

        self._curves = TemperatureCurves(profile)
        self._start_time = datetime.now()
        self._pid.reset()
        log.info("Firing profile selected: %s (%s)", name, self._curves.duration_formatted)

    def _on_ir_temp_set(self, ir_temp: float) -> None:
        """Handle IR pyrometer calibration input."""
        readings = self._sensors.read_all()
        tc_temp = readings.get("temperature_thermocouple")
        if tc_temp is not None:
            self._sensors.temp_approximator.update_ir(ir_temp, tc_temp)

    def _on_sensor_readings(self, readings: dict) -> None:
        """Log and display new sensor readings."""
        self._gui.update_technical_params(readings)
        self._gui.update_temperature_params(readings)
        self._logger.log(
            temperature=readings.get("temperature_thermocouple"),
            humidity=readings.get("humidity"),
            power=readings.get("power"),
        )

    # -- Control loop ---------------------------------------------------------

    def _control_loop(self) -> None:
        """PID → TRIAC output loop (runs in a background thread)."""
        while self._running:
            if self._curves is None or self._start_time is None:
                time.sleep(self.CONTROL_INTERVAL)
                continue

            readings = self._sensors.read_all()
            temp = readings.get("temperature_thermocouple", 0.0)

            elapsed = (datetime.now() - self._start_time).total_seconds()
            expected = self._curves.get_expected_temperature(int(elapsed))
            if expected is None:
                expected = 0.0

            # PID: setpoint = expected temperature, process = actual temperature
            self._pid.setpoint = expected
            power_output = self._pid.compute(temp)  # 0 … output_max ms

            # Convert PID output to TRIAC timing
            on_ms = power_output
            off_ms = max(0.0, self._half_cycle_ms - on_ms)
            self._triac.set_delays(on_ms=on_ms, off_ms=off_ms)

            # Feed expected temperature to the GUI
            readings["temperature_expected"] = f"{expected:.1f}"
            self._gui.update_temperature_params(readings)

            time.sleep(self.CONTROL_INTERVAL)

    def _update_loop(self) -> None:
        """Periodic GUI time/progress updates (runs in a background thread)."""
        while self._running:
            if self._start_time and self._curves:
                elapsed = datetime.now() - self._start_time
                total = timedelta(seconds=self._curves.duration_seconds)
                remaining = max(timedelta(), total - elapsed)
                final = self._start_time + total

                self._gui.update_times(
                    elapsed=str(elapsed).split(".")[0],
                    remaining=str(remaining).split(".")[0],
                    final=final.strftime("%H:%M:%S"),
                )

                pct = min(100.0, elapsed.total_seconds() / max(1, total.total_seconds()) * 100)
                self._gui.update_progress(pct)

            time.sleep(1.0)

    # -- Lifecycle ------------------------------------------------------------

    def start(self) -> None:
        """Start all subsystems and enter the GUI main loop."""
        self._running = True

        Thread(target=self._dispatcher.run, daemon=True).start()
        Thread(target=self._control_loop, daemon=True).start()
        Thread(target=self._update_loop, daemon=True).start()
        Thread(target=self._sensors.start_polling, daemon=True).start()

        self._triac.check_zero_cross()
        self._gui.run()  # blocks until window is closed

    def stop(self) -> None:
        """Shut down all subsystems cleanly."""
        self._running = False
        try:
            self._triac.stop()
            self._sensors.close()
            self._logger.close()
            self._dispatcher.stop()
        except Exception as exc:
            log.error("Error during shutdown: %s", exc)
