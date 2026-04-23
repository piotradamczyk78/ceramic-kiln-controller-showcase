"""Profile selection widget with progress bar."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List

from ceramique.ui.components.base_frame import BaseFrame


class ProfileSelector(BaseFrame):
    """Dropdown for selecting a firing profile and a progress bar."""

    def __init__(
        self,
        parent: tk.Widget,
        profiles: List[str],
        on_change: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        self._on_change = on_change

        self._profile_var = self._create_var("profile", profiles[0] if profiles else "")
        self._progress_var = self._create_var("progress", 0.0, "DoubleVar")
        self._progress_pct = self._create_var("progress_pct", "0 %")

        # Profile dropdown
        menu = tk.OptionMenu(
            self, self._profile_var, *profiles, command=self._on_change
        )
        menu.config(width=20)
        menu.pack(pady=(10, 10))

        # Progress bar
        style = ttk.Style()
        style.configure(
            "Kiln.Horizontal.TProgressbar",
            troughcolor="white",
            background="navy",
            thickness=25,
        )
        self._bar = ttk.Progressbar(
            self,
            variable=self._progress_var,
            maximum=100,
            style="Kiln.Horizontal.TProgressbar",
            length=500,
        )
        self._bar.pack(pady=(5, 5))

        self._pct_label = tk.Label(
            self, textvariable=self._progress_pct, fg="white", bg="navy"
        )
        self._pct_label.place(in_=self._bar, relx=0.5, rely=0.5, anchor="center")

    def update_profiles(self, profiles: List[str]) -> None:
        """Replace the dropdown options with a new list."""
        menu = self.children.get("!optionmenu")
        if menu:
            menu["menu"].delete(0, "end")
            for name in profiles:
                menu["menu"].add_command(
                    label=name, command=tk._setit(self._profile_var, name, self._on_change)
                )

    def update_progress(self, value: float) -> None:
        """Set the progress bar (0–100 %)."""
        self._progress_var.set(value)
        self._progress_pct.set(f"{value:.1f} %")
