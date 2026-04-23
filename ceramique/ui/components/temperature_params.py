"""Temperature parameters display with IR calibration input."""

import tkinter as tk
from typing import Any, Callable, Dict

from ceramique.ui.components.base_frame import BaseFrame


class TemperatureParams(BaseFrame):
    """Shows thermocouple, IR, approximate, and expected temperatures."""

    def __init__(
        self,
        parent: tk.Widget,
        on_ir_temp_set: Callable[[float], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        self._on_ir_temp_set = on_ir_temp_set

        # Read-only temperature displays
        self._tc = self._create_var("temperature_thermocouple", "0.0")
        self._approx = self._create_var("temperature_approximate", "0.0")
        self._expected = self._create_var("temperature_expected", "0.0")
        self._ambient = self._create_var("temperature_ambient", "0.0")
        self._humidity = self._create_var("humidity", "0.0")

        row = 0
        for label, var, color in [
            ("Thermocouple (°C):", self._tc, "black"),
            ("Approximate (°C):", self._approx, "maroon"),
            ("Expected (°C):", self._expected, "maroon"),
            ("Ambient (°C):", self._ambient, "black"),
            ("Humidity (%):", self._humidity, "black"),
        ]:
            tk.Label(self, text=label, anchor="e", fg=color).grid(
                row=row, column=0, padx=10, pady=5, sticky="e"
            )
            tk.Label(self, textvariable=var, anchor="w", fg=color).grid(
                row=row, column=1, padx=10, pady=5, sticky="w"
            )
            row += 1

        # IR pyrometer input with SET button
        self._ir_var = self._create_var("ir_input", 0.0, "DoubleVar")
        tk.Label(self, text="IR Pyrometer (°C):", anchor="e").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        spinbox = tk.Spinbox(
            self, from_=-100, to=1500, increment=1,
            textvariable=self._ir_var, width=6,
        )
        spinbox.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        tk.Button(
            self, text="SET",
            command=lambda: self._on_ir_temp_set(self._ir_var.get()),
        ).grid(row=row, column=2, padx=5, pady=5)

    def update_params(self, params: Dict[str, Any]) -> None:
        """Update displayed temperatures from a readings dict."""
        for key, value in params.items():
            var = self._get_var(key)
            if var is not None:
                var.set(f"{value:.1f}" if isinstance(value, float) else str(value))
