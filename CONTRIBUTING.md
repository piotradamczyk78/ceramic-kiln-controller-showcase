# Contributing to Ceramique

## Development Setup

```bash
# Clone and install dev dependencies
git clone https://github.com/octadecimal-ai/ceramique.git
cd ceramique
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

On macOS / x86 Linux the sensor stubs are loaded automatically — no Raspberry Pi hardware required for development.

## Code Style

- **Formatter**: [Black](https://black.readthedocs.io/) with `line-length = 100`
- **Type hints**: Required on all function signatures
- **Docstrings**: Google style, in English
- **No `print()` for debugging** — use `logging.getLogger(__name__)`
- **No bare `except:`** — always catch specific exceptions
- **Properties** over getters/setters
- **No hardcoded paths** — use `ConfigManager` or environment variables

## Branch Naming

```
feat/short-description     # New feature
fix/short-description      # Bug fix
refactor/short-description # Code refactoring
docs/short-description     # Documentation only
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new sensor driver
fix: correct PID integral accumulation
docs: update hardware wiring diagram
refactor: extract base frame class
test: add MAX31855 bit-parsing tests
```

## Pull Requests

1. Create a feature branch from `main`
2. Write code following the style guidelines above
3. Add or update tests if applicable
4. Open a PR with a clear description of what and why

## Testing

```bash
pytest                     # run all tests
pytest tests/test_pid.py   # run specific test file
pytest -v                  # verbose output
```

## Deploying to Raspberry Pi

```bash
# Set target (or edit defaults in sync.sh)
export RPI_HOST=192.0.2.42
export RPI_USER=pi

# Sync and install
./scripts/sync.sh

# Sync and start remote debugger
./scripts/sync.sh --debug
```
