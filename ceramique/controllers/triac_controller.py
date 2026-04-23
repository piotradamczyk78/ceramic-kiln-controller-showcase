"""TRIAC phase-angle power controller with zero-cross detection.

Controls a heating element by varying the TRIAC firing delay after each
AC zero-crossing.  A shorter delay means more of each half-cycle is
conducted, delivering more power to the load.

Timing diagram for one AC half-cycle (10 ms at 50 Hz):

    AC waveform:   ╭──╮      ╭──╮
                  ╱    ╲    ╱    ╲
    ─────────────╱──────╲──╱──────╲────
    zero-cross  ↑   on_delay   ↑
                │←──────→│     │
                          │←──→│
                         TRIAC on
"""

import time
from typing import Any

import lgpio


class TriacController:
    """GPIO-based TRIAC phase-angle controller."""

    def __init__(
        self,
        event_dispatcher: Any,
        gpio_config: dict[str, Any],
        power_config: dict[str, Any],
    ) -> None:
        """Initialize TRIAC and zero-cross detection GPIO pins.

        Args:
            event_dispatcher: Event bus for re-dispatching the polling
                function on each iteration.
            gpio_config: Must contain ``zero_cross_pin`` and ``triac_pin``.
            power_config: Must contain ``half_cycle_time`` (seconds).
        """
        self._dispatcher = event_dispatcher
        self._zc_pin: int = gpio_config["zero_cross_pin"]
        self._triac_pin: int = gpio_config["triac_pin"]
        self._half_cycle_ms: float = power_config.get("half_cycle_time", 0.01) * 1000

        self._handle = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self._handle, self._zc_pin)
        lgpio.gpio_claim_output(self._handle, self._triac_pin)

        self._on_delay_ms: float = 0.0
        self._off_delay_ms: float = 0.0
        self._armed = True  # prevents double-firing within a half-cycle

    def set_delays(self, on_ms: float, off_ms: float) -> None:
        """Set TRIAC firing timing for subsequent half-cycles.

        Args:
            on_ms: Delay from zero-cross to TRIAC gate pulse (milliseconds).
            off_ms: Duration the TRIAC remains off after the pulse.
        """
        self._on_delay_ms = on_ms
        self._off_delay_ms = off_ms

    def check_zero_cross(self) -> None:
        """Poll for a zero-crossing event and fire the TRIAC.

        This method dispatches itself back to the event queue so it
        runs continuously without blocking other event handlers.
        """
        if lgpio.gpio_read(self._handle, self._zc_pin) == 0 and self._armed:
            lgpio.gpio_write(self._handle, self._triac_pin, 1)
            time.sleep(self._on_delay_ms / 1000)
            lgpio.gpio_write(self._handle, self._triac_pin, 0)
            time.sleep(self._off_delay_ms / 1000)
            self._armed = False

        if lgpio.gpio_read(self._handle, self._zc_pin) == 1:
            self._armed = True

        self._dispatcher.dispatch(self.check_zero_cross)

    def stop(self) -> None:
        """Turn off the TRIAC and release GPIO resources."""
        lgpio.gpio_write(self._handle, self._triac_pin, 0)
        lgpio.gpiochip_close(self._handle)
