"""Multi-sensor orchestration with graceful degradation.

Each sensor is initialized independently inside its own ``try/except``
block.  If one sensor fails to initialize (or throws at read time),
the remaining sensors continue operating.  The ``sensor_status`` dict
tracks which sensors are currently live.
"""

import logging
import time
from typing import Any, Dict

from ceramique.processors.temperature_approximator import TemperatureApproximator

log = logging.getLogger(__name__)


class SensorManager:
    """Reads all kiln sensors and dispatches consolidated data."""

    def __init__(self, event_dispatcher: Any, config: Dict[str, Any]) -> None:
        """Initialize available sensors from *config*.

        Args:
            event_dispatcher: Event bus — readings are dispatched as
                ``"sensor_readings"`` events.
            config: Dict containing ``gpio``, ``hx711``, ``max31855``,
                ``sht31``, and ``pzem`` sub-dicts.
        """
        self._dispatcher = event_dispatcher
        self.sensor_status: Dict[str, bool] = {}
        self.polling_interval: float = 1.0
        self.temp_approximator = TemperatureApproximator()

        self._sht31 = self._init_sht31()
        self._pzem = self._init_pzem(config.get("pzem", {}))
        self._thermocouple = self._init_thermocouple(config.get("max31855", {}))
        self._load_cell = self._init_load_cell(config)

    # -- Initialization (each sensor isolated) --------------------------------

    def _init_sht31(self) -> Any:
        try:
            from ceramique.sensors import SHT31

            if SHT31 is None:
                raise ImportError("SHT31 not available on this platform")
            sensor = SHT31()
            self.sensor_status["sht31"] = True
            return sensor
        except Exception as exc:
            log.warning("SHT31 init failed: %s", exc)
            self.sensor_status["sht31"] = False
            return None

    def _init_pzem(self, pzem_cfg: Dict[str, Any]) -> Any:
        try:
            from ceramique.sensors import PZEM004T

            sensor = PZEM004T(
                port=pzem_cfg.get("uart_port", "/dev/ttyAMA0"),
                baudrate=pzem_cfg.get("baudrate", 9600),
                slave_id=pzem_cfg.get("modbus_address", 1),
            )
            self.sensor_status["pzem"] = True
            return sensor
        except Exception as exc:
            log.warning("PZEM-004T init failed: %s", exc)
            self.sensor_status["pzem"] = False
            return None

    def _init_thermocouple(self, tc_cfg: Dict[str, Any]) -> Any:
        try:
            from ceramique.sensors import MAX31855

            sensor = MAX31855(
                bus=tc_cfg.get("spi_bus", 0),
                device=tc_cfg.get("spi_device", 1),
                speed_hz=tc_cfg.get("spi_speed_hz", 5_000_000),
                corrections=tc_cfg.get("corrections"),
            )
            self.sensor_status["thermocouple"] = True
            return sensor
        except Exception as exc:
            log.warning("MAX31855 init failed: %s", exc)
            self.sensor_status["thermocouple"] = False
            return None

    def _init_load_cell(self, config: Dict[str, Any]) -> Any:
        try:
            from ceramique.sensors import HX711

            gpio = config.get("gpio", {}).get("hx711", {})
            hx_cfg = config.get("hx711", {})
            sensor = HX711(
                dout_pin=gpio["dout_pin"],
                pd_sck_pin=gpio["pd_sck_pin"],
                gain=hx_cfg.get("gain", 128),
            )
            sensor.tare()
            self.sensor_status["load_cell"] = True
            return sensor
        except Exception as exc:
            log.warning("HX711 init failed: %s", exc)
            self.sensor_status["load_cell"] = False
            return None

    # -- Reading --------------------------------------------------------------

    def read_all(self) -> Dict[str, Any]:
        """Read every live sensor and return a consolidated dict."""
        readings: Dict[str, Any] = {}

        if self._pzem and self.sensor_status["pzem"]:
            try:
                if self._pzem.read_data():
                    readings.update(
                        voltage=self._pzem.voltage,
                        current=self._pzem.current,
                        power=self._pzem.power,
                        energy=self._pzem.energy,
                    )
            except Exception:
                self.sensor_status["pzem"] = False

        if self._thermocouple and self.sensor_status["thermocouple"]:
            try:
                temp = self._thermocouple.temperature
                if temp is not None:
                    self.temp_approximator.update_thermocouple(temp)
                    readings["temperature_thermocouple"] = temp
                    readings["temperature_approximate"] = (
                        self.temp_approximator.temperature
                    )
            except Exception:
                self.sensor_status["thermocouple"] = False

        if self._sht31 and self.sensor_status["sht31"]:
            try:
                readings["temperature_ambient"] = self._sht31.temperature
                readings["humidity"] = self._sht31.humidity
            except Exception:
                self.sensor_status["sht31"] = False

        if self._load_cell and self.sensor_status["load_cell"]:
            try:
                w = self._load_cell.weight
                if w is not None:
                    readings["weight"] = w
            except Exception:
                self.sensor_status["load_cell"] = False

        return readings

    def update(self) -> Dict[str, Any]:
        """Read sensors and dispatch results as an event."""
        readings = self.read_all()
        self._dispatcher.dispatch("sensor_readings", readings)
        return readings

    def start_polling(self) -> None:
        """Continuously read sensors at :attr:`polling_interval`."""
        while True:
            self.update()
            time.sleep(self.polling_interval)

    # -- Calibration helpers --------------------------------------------------

    def calibrate_load_cell(self, known_weight: float) -> bool:
        """Calibrate the load cell with a reference weight (grams)."""
        if not self._load_cell or not self.sensor_status["load_cell"]:
            return False
        try:
            return self._load_cell.calibrate(known_weight)
        except Exception:
            return False

    def tare_load_cell(self) -> bool:
        """Zero the load cell."""
        if not self._load_cell or not self.sensor_status["load_cell"]:
            return False
        try:
            return self._load_cell.tare()
        except Exception:
            return False

    # -- Cleanup --------------------------------------------------------------

    def close(self) -> None:
        """Release resources held by all sensors."""
        if self._load_cell:
            self._load_cell.close()
        if self._pzem:
            self._pzem.close()
        if self._thermocouple:
            self._thermocouple.close()
