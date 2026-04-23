"""CSV telemetry data logger for kiln firing sessions.

Creates a timestamped CSV file per session with sensor readings.
Supports context-manager usage for automatic cleanup.

Usage::

    with DataLogger() as logger:
        logger.log(temperature=850.2, humidity=12.3, power=2400.0)
"""

import csv
from datetime import datetime
from typing import Optional


class DataLogger:
    """Appends kiln telemetry rows to a CSV file."""

    HEADER = [
        "timestamp",
        "temperature",
        "humidity",
        "voltage",
        "current",
        "power",
        "energy",
        "weight",
    ]

    def __init__(self, filename: Optional[str] = None) -> None:
        """Open (or create) a CSV log file.

        Args:
            filename: Output path. Defaults to
                ``kiln_data_YYYYMMDD_HHMMSS.csv`` in the working directory.
        """
        self._filename = filename or f"kiln_data_{datetime.now():%Y%m%d_%H%M%S}.csv"
        self._file = open(self._filename, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.HEADER)
        self._file.flush()

    def log(self, **kwargs: Optional[float]) -> None:
        """Write a single row of sensor data.

        Keyword arguments should match :attr:`HEADER` field names
        (excluding ``timestamp``).  Missing fields are written as empty
        strings.
        """
        row = [datetime.now().isoformat()]
        for field in self.HEADER[1:]:
            value = kwargs.get(field)
            row.append("" if value is None else str(value))
        self._writer.writerow(row)
        self._file.flush()

    def close(self) -> None:
        """Flush and close the CSV file."""
        if self._file and not self._file.closed:
            self._file.close()

    def __enter__(self) -> "DataLogger":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
