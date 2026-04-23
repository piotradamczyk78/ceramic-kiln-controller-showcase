"""Stateful PID temperature controller.

This controller MUST be instantiated once and called repeatedly so
that the integral and derivative terms accumulate properly.  Creating
a new instance on every control cycle (a bug found in an earlier
version) effectively reduces PID to proportional-only control.

Usage::

    pid = PIDController(kp=320, ki=160, kd=8, output_limits=(0, 500))
    pid.setpoint = 850.0

    while running:
        temperature = read_thermocouple()
        output_ms = pid.compute(temperature)   # 0 … 500 ms
        triac.set_delays(on_ms=output_ms, off_ms=half_cycle - output_ms)
        time.sleep(0.1)
"""

from simple_pid import PID


class PIDController:
    """Wrapper around ``simple-pid`` that enforces persistent state.

    The underlying :class:`simple_pid.PID` object stores integral
    accumulation and the previous error between calls.  This class
    exposes a minimal interface so the rest of the application does
    not depend on the library's API directly.
    """

    def __init__(
        self,
        kp: float = 320,
        ki: float = 160,
        kd: float = 8,
        setpoint: float = 0.0,
        output_limits: tuple[float, float] = (0, 500),
    ) -> None:
        """Create a PID controller.

        Args:
            kp: Proportional gain.
            ki: Integral gain.
            kd: Derivative gain.
            setpoint: Initial target temperature in °C.
            output_limits: Clamp the output to *(min, max)*.
                The default (0, 500) maps to TRIAC on-time in ms.
        """
        self._pid = PID(kp, ki, kd, setpoint=setpoint)
        self._pid.output_limits = output_limits

    @property
    def setpoint(self) -> float:
        """Target temperature in °C."""
        return self._pid.setpoint

    @setpoint.setter
    def setpoint(self, value: float) -> None:
        self._pid.setpoint = value

    def compute(self, current_value: float) -> float:
        """Compute the next PID output.

        Args:
            current_value: The current process variable (temperature).

        Returns:
            Control output clamped to *output_limits*.
        """
        return self._pid(current_value)

    @property
    def components(self) -> tuple[float, float, float]:
        """Current (proportional, integral, derivative) terms."""
        return self._pid.components

    def reset(self) -> None:
        """Clear accumulated integral and derivative state."""
        self._pid.reset()
