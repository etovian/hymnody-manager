import os
from pathlib import Path

import pytest

from src.config import DEFAULT_MUSIC_DIR, get_music_dir

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_default_music_dir_is_repo_root_music_folder():
    assert DEFAULT_MUSIC_DIR == REPO_ROOT / "music"


def test_default_music_dir_contains_no_windows_drive_or_separator():
    raw = str(DEFAULT_MUSIC_DIR)
    assert ":\\" not in raw
    assert "\\" not in raw
    assert "IdeaProjects" not in raw


def test_get_music_dir_defaults_to_repo_root_music_folder(monkeypatch):
    monkeypatch.delenv("MUSIC_DIR", raising=False)
    assert Path(get_music_dir()) == REPO_ROOT / "music"


def test_get_music_dir_honors_env_override(monkeypatch, tmp_path):
    override = tmp_path / "elsewhere"
    monkeypatch.setenv("MUSIC_DIR", str(override))
    assert Path(get_music_dir()) == override
