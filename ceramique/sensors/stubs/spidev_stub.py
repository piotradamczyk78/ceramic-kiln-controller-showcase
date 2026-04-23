"""Mock ``spidev.SpiDev`` for development on non-RPi platforms."""


class SpiDev:
    """Drop-in SPI stub that returns zeroed data."""

    def __init__(self) -> None:
        self.max_speed_hz: int = 0

    def open(self, bus: int, device: int) -> None:
        pass

    def xfer2(self, data: list[int]) -> list[int]:
        return [0x00] * len(data)

    def close(self) -> None:
        pass
