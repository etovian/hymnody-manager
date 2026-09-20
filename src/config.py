"""Shared configuration defaults resolved relative to the repository root.

Keeping the music directory default here (rather than a hardcoded absolute
path) lets the same checkout run on Windows and macOS without an env var,
which the dual-node Home/Church setup relies on.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MUSIC_DIR = REPO_ROOT / "music"


def get_music_dir():
    """Return the .m4a audio directory, honoring the MUSIC_DIR override."""
    return os.environ.get("MUSIC_DIR", str(DEFAULT_MUSIC_DIR))
