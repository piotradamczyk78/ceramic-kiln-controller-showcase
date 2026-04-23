"""Entry point for ``python -m ceramique``."""

import logging
import sys

from ceramique.controllers.kiln_controller import KilnController

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    try:
        kiln = KilnController()
        kiln.start()
    except KeyboardInterrupt:
        logging.info("Interrupted — shutting down")
    except Exception:
        logging.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
