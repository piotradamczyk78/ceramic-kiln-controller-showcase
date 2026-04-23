"""Real-time temperature plotting with matplotlib.

Displays the expected firing profile curve alongside the actual
measured temperature, updated live during a firing cycle.
"""

import tkinter as tk
from typing import Any, Dict, List, Optional

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class TemperaturePlot:
    """Matplotlib-based firing curve visualization embedded in Tkinter."""

    MAX_POINTS = 2000
    UPDATE_INTERVAL = 0.5  # seconds — minimum time between redraws

    def __init__(self, parent: tk.Widget) -> None:
        self._fig = Figure(figsize=(8, 4), dpi=100)
        self._ax = self._fig.add_subplot(111)

        self._ax.set_title("Firing Profile")
        self._ax.set_xlabel("Time (HH:MM)")
        self._ax.set_ylabel("Temperature (°C)")
        self._ax.grid(True)

        # Data buffers
        self._actual_times: List[float] = []
        self._actual_temps: List[float] = []
        self._profile_times: List[float] = []
        self._profile_temps: List[float] = []

        # Plot lines
        (self._line_actual,) = self._ax.plot([], [], "b-", label="Actual", linewidth=1.5)
        (self._line_profile,) = self._ax.plot([], [], "g:", label="Profile", linewidth=1.5)
        self._line_current = self._ax.axvline(
            x=0, color="r", linestyle="-", linewidth=1, alpha=0.6
        )

        self._ax.legend(loc="upper left")

        # X-axis formatter: seconds → HH:MM
        self._ax.xaxis.set_major_formatter(
            lambda x, _: f"{int(x // 3600):02d}:{int((x % 3600) // 60):02d}"
        )

        # Embed in Tkinter
        self._canvas = FigureCanvasTkAgg(self._fig, master=parent)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._last_draw: float = 0.0

    def draw_profile(self, profile: Dict[str, Any]) -> None:
        """Render the expected temperature profile curve.

        Args:
            profile: Firing profile dict with a ``points`` list containing
                ``time`` (HH:MM) and ``temperature`` entries.
        """
        self._profile_times.clear()
        self._profile_temps.clear()

        for point in profile.get("points", []):
            t = self._time_to_seconds(point["time"])
            self._profile_times.append(t)
            self._profile_temps.append(float(point["temperature"]))

        self._line_profile.set_data(self._profile_times, self._profile_temps)

        if self._profile_times:
            self._ax.set_xlim(0, max(self._profile_times))
            self._ax.set_ylim(0, max(self._profile_temps) * 1.1)

        name = profile.get("name", "Unknown")
        self._ax.set_title(f"Firing Profile — {name}")

        # Reset actual data when switching profiles
        self._actual_times.clear()
        self._actual_temps.clear()
        self._line_actual.set_data([], [])

        self._canvas.draw_idle()

    def update(self, elapsed_seconds: float, actual_temp: float) -> None:
        """Append a new actual-temperature data point and redraw.

        Args:
            elapsed_seconds: Seconds since the firing started.
            actual_temp: Current thermocouple reading (°C).
        """
        self._actual_times.append(elapsed_seconds)
        self._actual_temps.append(actual_temp)

        # Cap the number of stored points
        if len(self._actual_times) > self.MAX_POINTS:
            self._actual_times = self._actual_times[-self.MAX_POINTS:]
            self._actual_temps = self._actual_temps[-self.MAX_POINTS:]

        self._line_actual.set_data(self._actual_times, self._actual_temps)
        self._line_current.set_xdata([elapsed_seconds])

        self._canvas.draw_idle()

    def set_title(self, title: str) -> None:
        """Override the plot title."""
        self._ax.set_title(title)
        self._canvas.draw_idle()

    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        parts = time_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 3600 + int(parts[1]) * 60
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0.0
