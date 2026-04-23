"""Base frame with Tkinter variable management."""

import tkinter as tk
from typing import Any, Dict, Optional


class BaseFrame(tk.Frame):
    """Frame subclass with a helper for creating and retrieving Tk variables."""

    def __init__(self, parent: tk.Widget, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self._variables: Dict[str, tk.Variable] = {}

    def _create_var(
        self, name: str, value: Any = None, var_type: str = "StringVar"
    ) -> tk.Variable:
        """Create a named Tkinter variable.

        Args:
            name: Key used to look up the variable later.
            value: Initial value.
            var_type: One of ``StringVar``, ``DoubleVar``, ``IntVar``, ``BooleanVar``.
        """
        cls = getattr(tk, var_type)
        var = cls(value=value)
        self._variables[name] = var
        return var

    def _get_var(self, name: str) -> Optional[tk.Variable]:
        """Retrieve a previously created variable by *name*."""
        return self._variables.get(name)
