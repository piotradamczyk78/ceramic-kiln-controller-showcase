"""Technical parameters display — electrical and TRIAC timing."""

import tkinter as tk
from typing import Any, Dict

from ceramique.ui.components.base_frame import BaseFrame


class TechnicalParams(BaseFrame):
    """Grid of TRIAC cycle timing and electrical measurements."""

    _FIELDS = [
        ("cycle", "Cycle (ms):"),
        ("triac_on", "Triac on (ms):", "maroon"),
        ("voltage", "Voltage (V):"),
        ("current", "Current (A):"),
        ("power", "Power (W):", "maroon"),
        ("energy", "Energy (Wh):"),
    ]

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, **kwargs)

        for row, field in enumerate(self._FIELDS):
            name, label = field[0], field[1]
            color = field[2] if len(field) > 2 else "black"

            var = self._create_var(name, "0")
            tk.Label(self, text=label, anchor="e", fg=color).grid(
                row=row, column=0, padx=10, pady=5, sticky="e"
            )
            tk.Label(self, textvariable=var, anchor="w", fg=color).grid(
                row=row, column=1, padx=10, pady=5, sticky="w"
            )

    def update_params(self, params: Dict[str, Any]) -> None:
        """Update displayed values from a readings dict."""
        for key, value in params.items():
            var = self._get_var(key)
            if var is not None:
                var.set(str(value))
