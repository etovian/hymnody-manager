"""TSV Metadata Migration & Seed Data Generator script for LSB Hymns."""

import csv
from pathlib import Path


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


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    source_tsv = base_dir / "LSB Hymn Tracking (blank) - source.tsv"
    master_tsv = base_dir / "LSB Hymn Tracking (blank) - Master List.tsv"
    target_seed = base_dir / "src" / "lsb_seed_data.py"

    sources, tunes, catalog = parse_tsvs(str(source_tsv), str(master_tsv))
    generate_seed_data(sources, tunes, catalog, target_path=str(target_seed))
    print(
        f"Generated LSB seed data at {target_seed} with {len(sources)} sources, "
        f"{len(tunes)} tunes, and {len(catalog)} catalog entries."
    )
