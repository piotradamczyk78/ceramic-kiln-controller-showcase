"""Elapsed / remaining / final time display widget."""

import tkinter as tk

from ceramique.ui.components.base_frame import BaseFrame


class TimeInfo(BaseFrame):
    """Shows elapsed time, remaining time, and estimated finish time."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, **kwargs)

        self._elapsed = self._create_var("elapsed", "00:00:00")
        self._remaining = self._create_var("remaining", "00:00:00")
        self._final = self._create_var("final", "00:00:00")

        for row, (label, var) in enumerate(
            [
                ("Elapsed Time:", self._elapsed),
                ("Remaining Time:", self._remaining),
                ("Finish Time:", self._final),
            ]
        ):
            tk.Label(self, text=label, anchor="e").grid(
                row=row, column=0, padx=10, pady=5, sticky="e"
            )
            tk.Label(self, textvariable=var, anchor="w").grid(
                row=row, column=1, padx=10, pady=5, sticky="w"
            )

    def update_times(self, elapsed: str, remaining: str, final: str) -> None:
        """Refresh all three time displays at once."""
        self._elapsed.set(elapsed)
        self._remaining.set(remaining)
        self._final.set(final)
