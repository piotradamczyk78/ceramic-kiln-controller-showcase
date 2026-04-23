"""Temperature curve interpolation engine.

Given a firing profile (a sequence of time/temperature points) and
an elapsed time, computes the expected temperature via linear
interpolation between the two nearest profile points.

This is the primary input to the PID controller's setpoint — every
control cycle asks "what temperature should the kiln be at right now?"
"""

from typing import Any, Dict, List, Optional


class TemperatureCurves:
    """Interpolation engine for ceramic firing profiles."""

    def __init__(self, profile: Dict[str, Any]) -> None:
        """Prepare a profile for interpolation.

        Args:
            profile: Dict with a ``points`` list where each entry has
                ``time`` (``"HH:MM"`` or ``"HH:MM:SS"``) and
                ``temperature`` (numeric °C).
        """
        self._name = profile.get("name", "Unknown")
        self._times: List[int] = []
        self._temps: List[float] = []

        for point in profile.get("points", []):
            self._times.append(self._time_to_seconds(point["time"]))
            self._temps.append(float(point["temperature"]))

    # -- Public API -----------------------------------------------------------

    def get_expected_temperature(self, elapsed_seconds: int) -> Optional[float]:
        """Linearly interpolate the expected temperature at *elapsed_seconds*.

        Returns the boundary temperature when the time falls before
        the first point or after the last point.  Returns *None* if
        the profile has no points.
        """
        if not self._times:
            return None

        if elapsed_seconds <= self._times[0]:
            return self._temps[0]
        if elapsed_seconds >= self._times[-1]:
            return self._temps[-1]

        for i in range(len(self._times) - 1):
            t1, t2 = self._times[i], self._times[i + 1]
            if t1 <= elapsed_seconds <= t2:
                temp1, temp2 = self._temps[i], self._temps[i + 1]
                fraction = (elapsed_seconds - t1) / (t2 - t1)
                return temp1 + (temp2 - temp1) * fraction

        return None

    @property
    def duration_seconds(self) -> int:
        """Total duration of the profile in seconds."""
        return self._times[-1] if self._times else 0

    @property
    def duration_formatted(self) -> str:
        """Total duration as ``HH:MM:SS``."""
        return self._seconds_to_time(self.duration_seconds)

    @property
    def points(self) -> List[Dict[str, Any]]:
        """List of ``{time_seconds, temperature}`` dicts for plotting."""
        return [
            {"time_seconds": t, "temperature": temp}
            for t, temp in zip(self._times, self._temps)
        ]

    # -- Helpers --------------------------------------------------------------

    @staticmethod
    def _time_to_seconds(time_str: str) -> int:
        """Convert ``"HH:MM"`` or ``"HH:MM:SS"`` to total seconds."""
        parts = time_str.split(":")
        if len(parts) == 2:
            h, m = int(parts[0]), int(parts[1])
            return h * 3600 + m * 60
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            return h * 3600 + m * 60 + s
        raise ValueError(f"Invalid time format: {time_str!r}")

    @staticmethod
    def _seconds_to_time(seconds: int) -> str:
        """Convert total seconds to ``HH:MM:SS``."""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
