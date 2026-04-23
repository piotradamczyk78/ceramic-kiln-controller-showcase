"""Thread-safe event dispatcher using a queue-based pub/sub pattern.

Components register handlers for named events.  Any thread can dispatch
events; the :meth:`run` loop processes them sequentially from a shared
:class:`queue.Queue`.  Direct callables can also be dispatched for
one-shot scheduling (used by the TRIAC controller to re-enqueue its
polling function).
"""

import time
from queue import Queue, Empty
from typing import Any, Callable, Dict, List


class EventDispatcher:
    """Queue-based pub/sub event bus with support for named events and callables."""

    def __init__(self) -> None:
        self._queue: Queue[tuple[Any, tuple[Any, ...]]] = Queue()
        self._handlers: Dict[str, List[Callable[..., Any]]] = {}
        self._running = True

    def register(self, event_name: str, handler: Callable[..., Any]) -> None:
        """Subscribe *handler* to *event_name*."""
        self._handlers.setdefault(event_name, []).append(handler)

    def dispatch(self, event: Any, *args: Any) -> None:
        """Enqueue an event for processing.

        Args:
            event: A string event name (routed to registered handlers)
                or a callable (invoked directly by the run loop).
            *args: Positional arguments forwarded to the handler(s).
        """
        self._queue.put((event, args))

    def run(self) -> None:
        """Process events from the queue until :meth:`stop` is called."""
        while self._running:
            try:
                event, args = self._queue.get(timeout=0.05)
            except Empty:
                continue

            if callable(event):
                event(*args)
            elif isinstance(event, str):
                for handler in self._handlers.get(event, []):
                    handler(*args)

    def stop(self) -> None:
        """Signal the run loop to exit."""
        self._running = False
