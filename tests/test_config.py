import inspect
import os
from pathlib import Path

import pytest

from src.config import (
    DEFAULT_MAX_PRINTED_HYMN,
    DEFAULT_MUSIC_DIR,
    get_max_printed_hymn_number,
    get_music_dir,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_default_music_dir_is_repo_root_music_folder():
    assert DEFAULT_MUSIC_DIR == REPO_ROOT / "music"


def test_config_source_has_no_hardcoded_windows_path():
    import src.config
    source = inspect.getsource(src.config)
    assert r"c:\dev" not in source.lower()
    assert "c:/" not in source.lower()


def test_default_music_dir_posix_format_on_non_windows():
    if os.name != "nt":
        raw = str(DEFAULT_MUSIC_DIR)
        assert ":\\" not in raw
        assert "\\" not in raw


def test_get_music_dir_defaults_to_repo_root_music_folder(monkeypatch):
    monkeypatch.delenv("MUSIC_DIR", raising=False)
    assert Path(get_music_dir()) == REPO_ROOT / "music"


def test_get_music_dir_honors_env_override(monkeypatch, tmp_path):
    override = tmp_path / "elsewhere"
    monkeypatch.setenv("MUSIC_DIR", str(override))
    assert Path(get_music_dir()) == override


def test_default_max_printed_hymn(monkeypatch):
    monkeypatch.delenv("MAX_PRINTED_HYMN_NUMBER", raising=False)
    assert DEFAULT_MAX_PRINTED_HYMN == 966
    assert get_max_printed_hymn_number() == 966


def test_override_max_printed_hymn(monkeypatch):
    monkeypatch.setenv("MAX_PRINTED_HYMN_NUMBER", "950")
    assert get_max_printed_hymn_number() == 950


def test_invalid_max_printed_hymn_fallback(monkeypatch):
    monkeypatch.setenv("MAX_PRINTED_HYMN_NUMBER", "invalid_number")
    assert get_max_printed_hymn_number() == 966
