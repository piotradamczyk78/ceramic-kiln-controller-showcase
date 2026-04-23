"""Main Tkinter GUI window for the kiln controller.

Composes the profile selector, time info, technical parameters,
temperature parameters, and a finish button into a single window.
"""

import tkinter as tk
from typing import Any, Callable, Dict, List

from ceramique.ui.components.profile_selector import ProfileSelector
from ceramique.ui.components.time_info import TimeInfo
from ceramique.ui.components.technical_params import TechnicalParams
from ceramique.ui.components.temperature_params import TemperatureParams


class KilnGUI:
    """Top-level Tkinter application window."""

    def __init__(
        self,
        profile_names: List[str],
        on_profile_change: Callable[[str], None],
        on_ir_temp_set: Callable[[float], None],
        on_finish: Callable[[], None],
    ) -> None:
        self.root = tk.Tk()
        self.root.title("Ceramique Kiln Controller")

        main = tk.Frame(self.root)
        main.pack(padx=20, pady=20)

        self.profile_selector = ProfileSelector(main, profile_names, on_profile_change)
        self.profile_selector.pack(fill=tk.X, pady=(0, 15))

        self.time_info = TimeInfo(main)
        self.time_info.pack(fill=tk.X, pady=(0, 15))

        self.technical_params = TechnicalParams(main)
        self.technical_params.pack(fill=tk.X, pady=(0, 15))

        self.temperature_params = TemperatureParams(main, on_ir_temp_set)
        self.temperature_params.pack(fill=tk.X, pady=(0, 15))

        tk.Button(main, text="FINISH", command=on_finish, width=20, height=2).pack(
            pady=(0, 10)
        )

    # -- Delegated update methods --------------------------------------------

    def update_progress(self, value: float) -> None:
        """Update the firing progress bar (0–100 %)."""
        self.profile_selector.update_progress(value)

    def update_times(self, elapsed: str, remaining: str, final: str) -> None:
        """Refresh elapsed / remaining / finish time."""
        self.time_info.update_times(elapsed, remaining, final)

    def update_technical_params(self, params: Dict[str, Any]) -> None:
        """Update electrical and TRIAC timing values."""
        self.technical_params.update_params(params)

    def update_temperature_params(self, params: Dict[str, Any]) -> None:
        """Update all temperature displays."""
        self.temperature_params.update_params(params)

    def run(self) -> None:
        """Enter the Tkinter main loop (blocks)."""
        self.root.mainloop()
