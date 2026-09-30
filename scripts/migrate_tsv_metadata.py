"""TSV Metadata Migration & Seed Data Generator script for LSB Hymns."""

import argparse
import csv
import importlib
from pathlib import Path
import sys

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def parse_tsvs(source_tsv_path, master_tsv_path):
    """Parse LSB source mapping and master list TSVs.

    Returns:
        tuple: (sources, tunes, catalog)
            - sources: dict mapping source code to full meaning (str -> str)
            - tunes: set of unique hymn tune names (set of str)
            - catalog: dict mapping hymn number (int) to dict containing
                       title, source, tune, section.
    """
    sources = {}
    with open(source_tsv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        for row in reader:
            if not row or len(row) < 2:
                continue
            code = row[0].strip()
            meaning = row[1].strip()
            if code:
                sources[code] = meaning

    tunes = set()
    catalog = {}
    with open(master_tsv_path, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
        header_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith("Section\t") or "Hymn\tTitle" in line:
                header_idx = idx
                break

        reader_lines = lines[header_idx + 1 :] if header_idx != -1 else lines
        reader = csv.reader(reader_lines, delimiter="\t")
        for row in reader:
            if not row or len(row) < 5 or not row[1].strip():
                continue
            section = row[0].strip()
            hymn_raw = row[1].strip()
            try:
                hymn_num = int(hymn_raw)
            except ValueError:
                hymn_num = hymn_raw

            title = row[2].strip()
            source = row[3].strip()
            tune = row[4].strip()

            if tune:
                tunes.add(tune)

            catalog[hymn_num] = {
                "title": title,
                "source": source,
                "tune": tune,
                "section": section,
            }

    return sources, tunes, catalog


def generate_seed_data(sources, tunes, catalog, target_path="src/lsb_seed_data.py"):
    """Generate a static Python seed file containing SOURCES, TUNES, and HYMN_CATALOG."""
    sorted_tunes = sorted(list(tunes)) if isinstance(tunes, (set, list)) else list(tunes)

    lines = [
        '"""Auto-generated LSB Seed Data from TSV migration."""',
        "",
        f"SOURCES = {repr(sources)}",
        "",
        f"TUNES = {repr(sorted_tunes)}",
        "",
        f"HYMN_CATALOG = {repr(catalog)}",
        "",
    ]

    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main(sys_args=None, base_dir=None):
    parser = argparse.ArgumentParser(description="Migrate LSB TSV metadata to seed data and database.")
    parser.add_argument("--auto-confirm", "-y", action="store_true", help="Execute non-interactively without prompt.")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Remove TSV files after migration.")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip removing TSV files after migration.")
    parser.add_argument("--db-path", default="hymnody.db", help="Path to SQLite database (default: hymnody.db).")
    args = parser.parse_args(sys_args)

    if base_dir is None:
        base_dir = BASE_DIR
    else:
        base_dir = Path(base_dir)

    source_tsv = base_dir / "LSB Hymn Tracking (blank) - source.tsv"
    master_tsv = base_dir / "LSB Hymn Tracking (blank) - Master List.tsv"
    target_seed = base_dir / "src" / "lsb_seed_data.py"

    tsv_parsed = False
    if source_tsv.exists() and master_tsv.exists():
        try:
            sources, tunes, catalog = parse_tsvs(str(source_tsv), str(master_tsv))
            generate_seed_data(sources, tunes, catalog, target_path=str(target_seed))
            print(
                f"Generated LSB seed data at {target_seed} with {len(sources)} sources, "
                f"{len(tunes)} tunes, and {len(catalog)} catalog entries."
            )
            tsv_parsed = True
        except Exception as e:
            print(f"Error parsing TSVs or generating seed data: {e}", file=sys.stderr)
            tsv_parsed = False
    else:
        print("TSV source files not found; skipping TSV parsing and using existing seed data.")

    # Refresh seed module if loaded
    if "src.lsb_seed_data" in sys.modules:
        try:
            importlib.reload(sys.modules["src.lsb_seed_data"])
        except Exception:
            pass

    # Perform DB initialization and migration
    from src.database import init_db
    db_path_obj = Path(args.db_path)
    db_file = db_path_obj if db_path_obj.is_absolute() else base_dir / db_path_obj
    init_db(str(db_file))
    print(f"Migrated database schema and seed data at {db_file}.")

    # TSV cleanup
    if tsv_parsed:
        if args.no_cleanup:
            should_cleanup = False
        elif args.auto_confirm or args.cleanup:
            should_cleanup = True
        else:
            resp = input("Delete original .tsv files? (y/n): ").strip().lower()
            should_cleanup = resp in ("y", "yes")

        if should_cleanup:
            removed = []
            if source_tsv.exists():
                source_tsv.unlink()
                removed.append(source_tsv.name)
            if master_tsv.exists():
                master_tsv.unlink()
                removed.append(master_tsv.name)
            if removed:
                print(f"Cleaned up TSV files: {', '.join(removed)}")


if __name__ == "__main__":
    main()
