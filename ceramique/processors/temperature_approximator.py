"""IR pyrometer calibration for thermocouple temperature correction.

The thermocouple tip may not be positioned at the exact hottest point
inside the kiln.  A one-time IR pyrometer reading aimed at the firing
zone establishes an offset that is applied to all subsequent
thermocouple readings, producing a closer approximation of the true
kiln temperature.

Usage::

    approx = TemperatureApproximator()
    # User points IR gun at the kiln interior and reads 920 °C
    # while the thermocouple shows 895 °C
    approx.update_ir(ir_temp=920.0, thermocouple_temp=895.0)
    # offset = +25 °C

    # Later, thermocouple reads 910 °C → approximate = 935 °C
    approx.update_thermocouple(910.0)
    print(approx.temperature)  # 935.0
"""

from typing import Optional


class TemperatureApproximator:
    """Offset-based thermocouple correction using an IR reference point."""

    def __init__(self) -> None:
        self._ir_temperature: Optional[float] = None
        self._offset: float = 0.0
        self._approximate: Optional[float] = None

    def update_ir(self, ir_temp: float, thermocouple_temp: float) -> None:
        """Set the IR calibration point and compute the correction offset.

        Args:
            ir_temp: Temperature read by the IR pyrometer (°C).
            thermocouple_temp: Simultaneous thermocouple reading (°C).
        """
        self._ir_temperature = ir_temp
        self._offset = ir_temp - thermocouple_temp
        self._approximate = ir_temp

    def update_thermocouple(self, thermocouple_temp: float) -> None:
        """Update the approximation with a new thermocouple reading.

        If no IR calibration has been performed yet, the raw
        thermocouple value is used as-is.
        """
        if self._ir_temperature is not None:
            self._approximate = thermocouple_temp + self._offset
        else:
            self._approximate = thermocouple_temp

    @property
    def temperature(self) -> Optional[float]:
        """Current approximated kiln temperature in °C."""
        return self._approximate
