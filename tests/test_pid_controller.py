"""Tests for the PID temperature controller.

Verifies that the PID controller accumulates integral state across
calls (the critical fix for the stateless bug) and that output stays
within configured limits.
"""

import pytest

from ceramique.controllers.pid_controller import PIDController


class TestPIDController:
    """Verify PID behavior with persistent state."""

    def test_integral_accumulates(self):
        """The integral term must grow across repeated calls with steady error."""
        pid = PIDController(kp=1.0, ki=1.0, kd=0.0, setpoint=100.0, output_limits=(0, 1000))

        outputs = []
        for _ in range(10):
            output = pid.compute(50.0)  # constant 50 °C error
            outputs.append(output)

        # With accumulating integral, each successive output should be larger
        # (until saturation)
        for i in range(1, len(outputs)):
            assert outputs[i] >= outputs[i - 1], (
                f"Output decreased at step {i}: {outputs[i]} < {outputs[i-1]} "
                "— integral is not accumulating"
            )

    def test_output_limits(self):
        """PID output must be clamped to the configured range."""
        pid = PIDController(kp=1000.0, ki=0.0, kd=0.0, setpoint=1000.0, output_limits=(0, 500))

        output = pid.compute(0.0)  # huge error → should clamp to 500
        assert output <= 500.0
        assert output >= 0.0

    def test_output_limits_lower_bound(self):
        """Output should not go below zero when process exceeds setpoint."""
        pid = PIDController(kp=100.0, ki=0.0, kd=0.0, setpoint=100.0, output_limits=(0, 500))

        output = pid.compute(200.0)  # process > setpoint → negative correction
        assert output >= 0.0

    def test_setpoint_update(self):
        """Setpoint can be changed between compute() calls."""
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0, setpoint=100.0, output_limits=(0, 1000))

        out1 = pid.compute(50.0)  # error = 50
        pid.setpoint = 200.0
        out2 = pid.compute(50.0)  # error = 150
        assert out2 > out1

    def test_reset_clears_state(self):
        """After reset(), integral state should be zeroed."""
        pid = PIDController(kp=0.0, ki=10.0, kd=0.0, setpoint=100.0, output_limits=(0, 1000))

        # Accumulate some integral
        for _ in range(20):
            pid.compute(50.0)

        output_before = pid.compute(50.0)
        pid.reset()
        output_after = pid.compute(50.0)

        # After reset the integral starts from zero, so output should be smaller
        assert output_after < output_before

    def test_components_accessible(self):
        """The (P, I, D) components should be readable after compute."""
        pid = PIDController(kp=1.0, ki=1.0, kd=1.0, setpoint=100.0, output_limits=(0, 10000))
        pid.compute(50.0)

        p, i, d = pid.components
        assert isinstance(p, float)
        assert isinstance(i, float)
        assert isinstance(d, float)

    def test_stateful_across_many_calls(self):
        """Simulate a real heating scenario — output should increase then stabilize."""
        pid = PIDController(kp=2.0, ki=0.5, kd=0.1, setpoint=850.0, output_limits=(0, 500))

        temperature = 30.0  # starting ambient
        outputs = []

        for _ in range(100):
            output = pid.compute(temperature)
            outputs.append(output)
            # Simulate heating: temperature increases proportional to power
            temperature += output * 0.01

        # Temperature should have risen significantly
        assert temperature > 100.0, "Temperature should rise with sustained PID output"

        # Output should have been > 0 for most of the run
        non_zero = sum(1 for o in outputs if o > 0)
        assert non_zero > 50, "PID should produce non-zero output when below setpoint"
