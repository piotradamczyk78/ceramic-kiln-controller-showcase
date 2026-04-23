"""PZEM-004T AC power monitoring module — Modbus RTU driver.

Reads voltage, current, power, energy, frequency, and power factor
from the PZEM-004T module over a UART serial connection using the
Modbus RTU protocol.

Register map (input registers, function code 0x04):
    0x0000          Voltage (1 register, ÷10 → V)
    0x0001–0x0002   Current (2 registers, ÷1000 → A)
    0x0003–0x0004   Power   (2 registers, ÷10 → W)
    0x0005–0x0006   Energy  (2 registers, ÷1 → Wh)
    0x0007          Frequency    (1 register, ÷10 → Hz)
    0x0008          Power factor (1 register, ÷100)
    0x0009          Alarm status (1 register)
"""

from typing import List

from pymodbus.client import ModbusSerialClient
from pymodbus.framer import FramerType


class PZEM004T:
    """Modbus RTU driver for the PZEM-004T AC power meter."""

    def __init__(
        self,
        port: str = "/dev/ttyAMA0",
        baudrate: int = 9600,
        slave_id: int = 1,
        timeout: float = 1.0,
    ):
        """Open a Modbus RTU connection to the PZEM-004T.

        Args:
            port: Serial port device path.
            baudrate: UART baud rate (PZEM-004T default is 9600).
            slave_id: Modbus slave address (factory default 1).
            timeout: Read timeout in seconds.

        Raises:
            ConnectionError: If the serial connection cannot be opened.
        """
        self._slave_id = slave_id
        self._client = ModbusSerialClient(
            port=port,
            framer=FramerType.RTU,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=timeout,
        )

        if not self._client.connect():
            raise ConnectionError(f"Failed to connect to PZEM-004T on {port}")

        self._voltage: float = 0.0
        self._current: float = 0.0
        self._power: float = 0.0
        self._energy: int = 0
        self._frequency: float = 0.0
        self._power_factor: float = 0.0
        self._alarm: int = 0

    # -- Properties ----------------------------------------------------------

    @property
    def voltage(self) -> float:
        """AC voltage in volts."""
        return self._voltage

    @property
    def current(self) -> float:
        """AC current in amperes."""
        return self._current

    @property
    def power(self) -> float:
        """Active power in watts."""
        return self._power

    @property
    def energy(self) -> int:
        """Cumulative energy in watt-hours."""
        return self._energy

    @property
    def frequency(self) -> float:
        """AC frequency in hertz."""
        return self._frequency

    @property
    def power_factor(self) -> float:
        """Power factor (0.00–1.00)."""
        return self._power_factor

    @property
    def alarm(self) -> int:
        """Alarm status flag."""
        return self._alarm

    # -- Data acquisition ----------------------------------------------------

    def read_data(self) -> bool:
        """Read all measurement registers from the PZEM-004T.

        Returns:
            *True* if the read succeeded and properties are updated.
        """
        result = self._client.read_input_registers(
            0x00, count=10, slave=self._slave_id
        )
        if result.isError():
            return False

        regs = result.registers
        self._voltage = self._parse(regs[0:1], 10)
        self._current = self._parse(regs[1:3], 1000)
        self._power = self._parse(regs[3:5], 10)
        self._energy = int(self._parse(regs[5:7], 1))
        self._frequency = self._parse(regs[7:8], 10)
        self._power_factor = self._parse(regs[8:9], 100)
        self._alarm = int(self._parse(regs[9:10], 1))
        return True

    def close(self) -> None:
        """Close the Modbus serial connection."""
        self._client.close()

    # -- Helpers -------------------------------------------------------------

    @staticmethod
    def _parse(registers: List[int], divisor: int) -> float:
        """Convert one or two 16-bit Modbus registers to a scaled float.

        For two-register (32-bit) values the PZEM-004T stores the low
        word first: ``value = (high_register << 16) | low_register``.
        """
        if len(registers) == 1:
            return registers[0] / divisor
        if len(registers) == 2:
            raw = (registers[1] << 16) | registers[0]
            return raw / divisor
        return 0.0
