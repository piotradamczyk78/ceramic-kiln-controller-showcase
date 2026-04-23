"""SHT31-D I2C temperature and humidity sensor driver.

Wraps the Adafruit CircuitPython SHT31D library, providing a clean
interface for ambient temperature, relative humidity, and the built-in
heater (used to clear condensation from the sensor element).
"""

import board
import busio
import adafruit_sht31d


class SHT31:
    """I2C driver for the Sensirion SHT31-D temperature/humidity sensor."""

    def __init__(self) -> None:
        """Initialize I2C bus and SHT31-D sensor."""
        self._i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = adafruit_sht31d.SHT31D(self._i2c)

    @property
    def temperature(self) -> float:
        """Ambient temperature in °C."""
        return self._sensor.temperature

    @property
    def humidity(self) -> float:
        """Relative humidity in percent."""
        return self._sensor.relative_humidity

    @property
    def heater(self) -> bool:
        """Whether the internal heater is currently on."""
        return self._sensor.heater

    @heater.setter
    def heater(self, enabled: bool) -> None:
        """Enable or disable the internal heater.

        The heater raises the sensor element temperature by ~10 °C
        to evaporate condensation.  It should not be left on
        continuously — Sensirion recommends < 10 % duty cycle.
        """
        self._sensor.heater = enabled
