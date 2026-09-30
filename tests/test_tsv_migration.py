import sys
import importlib
from pathlib import Path
import pytest

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.migrate_tsv_metadata import parse_tsvs, generate_seed_data, main


def test_parse_tsvs(tmp_path):
    source_tsv = tmp_path / "source.tsv"
    source_tsv.write_text("Code\tMeaning\nLu\tLuther\nRC1900\tRoman Catholic hymns to 1900\n", encoding="utf-8")
    master_tsv = tmp_path / "master.tsv"
    master_tsv.write_text("Section\tHymn\tTitle\tSource\tTune\nAdvent\t331\tThe Advent of Our King\tRC1900\tSt. Thomas\n", encoding="utf-8")

    sources, tunes, catalog = parse_tsvs(str(source_tsv), str(master_tsv))

    assert len(sources) >= 1
    assert sources.get("Lu") == "Luther"
    assert "St. Thomas" in tunes

    entry = catalog.get(331) or catalog.get("331")
    assert entry is not None
    assert entry["title"] == "The Advent of Our King"
    assert entry["tune"] == "St. Thomas"
    assert entry["source"] == "RC1900"


def test_generate_seed_data(tmp_path):
    source_tsv = tmp_path / "source.tsv"
    source_tsv.write_text("Code\tMeaning\nLu\tLuther\nRC1900\tRoman Catholic hymns to 1900\n", encoding="utf-8")
    master_tsv = tmp_path / "master.tsv"
    master_tsv.write_text("Section\tHymn\tTitle\tSource\tTune\nAdvent\t331\tThe Advent of Our King\tRC1900\tSt. Thomas\n", encoding="utf-8")

    sources, tunes, catalog = parse_tsvs(str(source_tsv), str(master_tsv))

    target_seed = tmp_path / "lsb_seed_data.py"
    generate_seed_data(sources, tunes, catalog, target_path=str(target_seed))

    assert target_seed.exists()

    seed_content = target_seed.read_text(encoding="utf-8")
    assert "SOURCES =" in seed_content
    assert "TUNES =" in seed_content
    assert "HYMN_CATALOG =" in seed_content
    assert "Luther" in seed_content


def create_mock_tsvs(directory: Path):
    source_tsv = directory / "LSB Hymn Tracking (blank) - source.tsv"
    master_tsv = directory / "LSB Hymn Tracking (blank) - Master List.tsv"
    source_tsv.write_text("Code\tMeaning\nLu\tLuther\nRC1900\tRoman Catholic hymns to 1900\n", encoding="utf-8")
    master_tsv.write_text("Section\tHymn\tTitle\tSource\tTune\nAdvent\t331\tThe Advent of Our King\tRC1900\tSt. Thomas\n", encoding="utf-8")
    return source_tsv, master_tsv


def test_main_no_cleanup(tmp_path):
    source_tsv, master_tsv = create_mock_tsvs(tmp_path)
    db_path = tmp_path / "custom.db"

    main(["--no-cleanup", "--db-path", str(db_path)], base_dir=tmp_path)

    assert source_tsv.exists()
    assert master_tsv.exists()
    assert db_path.exists()
    assert (tmp_path / "src" / "lsb_seed_data.py").exists()


def test_main_auto_confirm(tmp_path):
    source_tsv, master_tsv = create_mock_tsvs(tmp_path)
    db_path = tmp_path / "custom.db"

    main(["--auto-confirm", "--db-path", str(db_path)], base_dir=tmp_path)

    assert not source_tsv.exists()
    assert not master_tsv.exists()
    assert db_path.exists()


def test_main_cleanup_flag(tmp_path):
    source_tsv, master_tsv = create_mock_tsvs(tmp_path)
    db_path = tmp_path / "custom.db"

    main(["-c", "--db-path", str(db_path)], base_dir=tmp_path)

    assert not source_tsv.exists()
    assert not master_tsv.exists()
    assert db_path.exists()


def test_main_interactive_prompt_yes(tmp_path, monkeypatch):
    source_tsv, master_tsv = create_mock_tsvs(tmp_path)
    db_path = tmp_path / "custom.db"

    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    main(["--db-path", str(db_path)], base_dir=tmp_path)

    assert not source_tsv.exists()
    assert not master_tsv.exists()


def test_main_interactive_prompt_no(tmp_path, monkeypatch):
    source_tsv, master_tsv = create_mock_tsvs(tmp_path)
    db_path = tmp_path / "custom.db"

    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    main(["--db-path", str(db_path)], base_dir=tmp_path)

    assert source_tsv.exists()
    assert master_tsv.exists()


def test_main_missing_tsv_skips_cleanup(tmp_path):
    db_path = tmp_path / "custom.db"
    main(["--cleanup", "--db-path", str(db_path)], base_dir=tmp_path)
    assert db_path.exists()
