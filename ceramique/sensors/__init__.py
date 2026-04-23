"""Sensor drivers — platform-aware imports.

On Raspberry Pi (armv7l / aarch64 Linux) the real hardware drivers
are loaded.  On development machines the stubs provide the same API
with simulated data so the application can run without GPIO hardware.
"""

import platform

_is_rpi = platform.system() == "Linux" and platform.machine() in ("armv7l", "aarch64")

if _is_rpi:
    from .hx711 import HX711
    from .max31855 import MAX31855
    from .sht31 import SHT31
else:
    from .stubs.hx711_stub import HX711  # type: ignore[assignment]

    # Patch spidev before importing MAX31855 so it works without real SPI
    import sys
    from .stubs import spidev_stub

    sys.modules.setdefault("spidev", spidev_stub)
    from .max31855 import MAX31855  # noqa: E402

    SHT31 = None  # type: ignore[assignment, misc]

from .pzem004t import PZEM004T

__all__ = ["HX711", "MAX31855", "PZEM004T", "SHT31"]
