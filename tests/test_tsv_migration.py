import sys
import importlib
from pathlib import Path
import pytest

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.migrate_tsv_metadata import parse_tsvs, generate_seed_data


def test_parse_tsvs(tmp_path):
    source_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - source.tsv"
    master_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - Master List.tsv"

    if not source_tsv.exists() or not master_tsv.exists():
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
    source_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - source.tsv"
    master_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - Master List.tsv"

    if not source_tsv.exists() or not master_tsv.exists():
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

