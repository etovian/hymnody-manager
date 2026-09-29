import sys
import importlib
from pathlib import Path
import pytest

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.migrate_tsv_metadata import parse_tsvs, generate_seed_data


def test_parse_tsvs():
    source_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - source.tsv"
    master_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - Master List.tsv"

    sources, tunes, catalog = parse_tsvs(str(source_tsv), str(master_tsv))

    assert len(sources) > 30
    assert sources.get("Lu") == "Luther"

    assert "St. Thomas" in tunes

    entry = catalog.get(331) or catalog.get("331")
    assert entry is not None
    assert entry["title"] == "The Advent of Our King"
    assert entry["tune"] == "St. Thomas"
    assert entry["source"] == "RC1900"


def test_generate_seed_data():
    source_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - source.tsv"
    master_tsv = BASE_DIR / "LSB Hymn Tracking (blank) - Master List.tsv"

    sources, tunes, catalog = parse_tsvs(str(source_tsv), str(master_tsv))

    target_seed = BASE_DIR / "src" / "lsb_seed_data.py"
    generate_seed_data(sources, tunes, catalog, target_path=str(target_seed))

    assert target_seed.exists()

    import src.lsb_seed_data
    importlib.reload(src.lsb_seed_data)

    assert hasattr(src.lsb_seed_data, "SOURCES")
    assert hasattr(src.lsb_seed_data, "TUNES")
    assert hasattr(src.lsb_seed_data, "HYMN_CATALOG")

    assert src.lsb_seed_data.SOURCES.get("Lu") == "Luther"
    assert "St. Thomas" in src.lsb_seed_data.TUNES
    cat_entry = src.lsb_seed_data.HYMN_CATALOG.get(331) or src.lsb_seed_data.HYMN_CATALOG.get("331")
    assert cat_entry is not None
    assert cat_entry["title"] == "The Advent of Our King"
    assert cat_entry["tune"] == "St. Thomas"
    assert cat_entry["source"] == "RC1900"
