"""Firing profile manager — loads, validates, and persists JSON profiles.

Each profile defines a sequence of time/temperature points that the
kiln controller follows during a firing.  Profiles are stored as
individual ``.json`` files in the curves directory.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class ProfileManager:
    """CRUD manager for ceramic firing profiles."""

    def __init__(self, curves_dir: Optional[str] = None) -> None:
        """Load all profiles from *curves_dir*.

        Args:
            curves_dir: Directory containing ``*.json`` profile files.
                Defaults to ``profiles/curves`` relative to this module.
        """
        if curves_dir is None:
            curves_dir = str(Path(__file__).parent / "curves")

        self._curves_dir = curves_dir
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Scan the curves directory and load every valid JSON profile."""
        if not os.path.isdir(self._curves_dir):
            log.warning("Curves directory not found: %s", self._curves_dir)
            return

        for filename in sorted(os.listdir(self._curves_dir)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self._curves_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    profile = json.load(fh)
                if "name" in profile and "points" in profile:
                    self._profiles[profile["name"]] = profile
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Skipping %s: %s", filename, exc)

    # -- Queries --------------------------------------------------------------

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the profile with the given *name*, or *None*."""
        return self._profiles.get(name)

    @property
    def names(self) -> List[str]:
        """Sorted list of all loaded profile names."""
        return sorted(self._profiles)

    @property
    def profiles(self) -> List[Dict[str, Any]]:
        """All loaded profiles as a list."""
        return list(self._profiles.values())

    # -- Mutations ------------------------------------------------------------

    def add(self, profile: Dict[str, Any]) -> bool:
        """Persist a new profile to disk.

        Args:
            profile: Must contain ``name`` (str) and ``points`` (list).

        Returns:
            *True* if the profile was saved successfully.
        """
        name = profile.get("name", "")
        if not name or "points" not in profile:
            return False

        filename = name.lower().replace(" ", "_") + ".json"
        path = os.path.join(self._curves_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(profile, fh, indent=2, ensure_ascii=False)
            self._profiles[name] = profile
            return True
        except OSError as exc:
            log.error("Failed to save profile %s: %s", name, exc)
            return False

    def delete(self, name: str) -> bool:
        """Remove a profile from disk and memory.

        Returns:
            *True* if the profile existed and was deleted.
        """
        if name not in self._profiles:
            return False

        filename = name.lower().replace(" ", "_") + ".json"
        path = os.path.join(self._curves_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as exc:
            log.error("Failed to delete %s: %s", path, exc)
            return False

        del self._profiles[name]
        return True
