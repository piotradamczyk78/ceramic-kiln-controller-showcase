"""Tests for the PZEM-004T Modbus RTU register parsing.

Mocks the Modbus client to verify register-to-float conversion logic.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPZEM004TParser:
    """Verify register parsing without a real serial connection."""

    def test_single_register_parsing(self):
        """Single 16-bit register divided by factor."""
        from ceramique.sensors.pzem004t import PZEM004T

        # 2301 / 10 = 230.1 V
        assert PZEM004T._parse([2301], 10) == pytest.approx(230.1)

    def test_dual_register_parsing(self):
        """Two 16-bit registers combined into 32-bit value."""
        from ceramique.sensors.pzem004t import PZEM004T

        # Low word = 1000, High word = 0 → value = 1000 / 10 = 100.0 W
        assert PZEM004T._parse([1000, 0], 10) == pytest.approx(100.0)

    def test_dual_register_high_word(self):
        """32-bit value where the high word is non-zero."""
        from ceramique.sensors.pzem004t import PZEM004T

        # Low = 0, High = 1 → value = (1 << 16) / 1 = 65536
        assert PZEM004T._parse([0, 1], 1) == pytest.approx(65536.0)

    def test_current_precision(self):
        """Current register divided by 1000."""
        from ceramique.sensors.pzem004t import PZEM004T

        # 5230 / 1000 = 5.23 A (low word only, high word = 0)
        assert PZEM004T._parse([5230, 0], 1000) == pytest.approx(5.23)

    def test_power_factor(self):
        """Power factor register divided by 100."""
        from ceramique.sensors.pzem004t import PZEM004T

        # 98 / 100 = 0.98
        assert PZEM004T._parse([98], 100) == pytest.approx(0.98)

    def test_empty_registers(self):
        """Empty register list returns 0."""
        from ceramique.sensors.pzem004t import PZEM004T

        assert PZEM004T._parse([], 10) == 0.0

    @patch("ceramique.sensors.pzem004t.ModbusSerialClient")
    def test_read_data_success(self, mock_client_cls):
        """Verify read_data() populates all properties correctly."""
        from ceramique.sensors.pzem004t import PZEM004T

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client_cls.return_value = mock_client

        # Simulate register response
        mock_result = MagicMock()
        mock_result.isError.return_value = False
        mock_result.registers = [
            2301,  # voltage: 230.1 V
            5230, 0,  # current: 5.230 A
            12000, 0,  # power: 1200.0 W
            500, 0,  # energy: 500 Wh
            500,  # frequency: 50.0 Hz
            98,  # power factor: 0.98
            0,  # alarm: 0
        ]
        mock_client.read_input_registers.return_value = mock_result

        sensor = PZEM004T()
        assert sensor.read_data() is True
        assert sensor.voltage == pytest.approx(230.1)
        assert sensor.current == pytest.approx(5.230)
        assert sensor.power == pytest.approx(1200.0)
        assert sensor.energy == 500
        assert sensor.frequency == pytest.approx(50.0)
        assert sensor.power_factor == pytest.approx(0.98)
        assert sensor.alarm == 0

    @patch("ceramique.sensors.pzem004t.ModbusSerialClient")
    def test_read_data_error(self, mock_client_cls):
        """read_data() returns False on Modbus error."""
        from ceramique.sensors.pzem004t import PZEM004T

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client_cls.return_value = mock_client

        mock_result = MagicMock()
        mock_result.isError.return_value = True
        mock_client.read_input_registers.return_value = mock_result

        sensor = PZEM004T()
        assert sensor.read_data() is False
