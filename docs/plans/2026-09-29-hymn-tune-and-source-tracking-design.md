# LSB Hymn Tune & Historical Source Tracking Design Document

## Overview
This design document details the normalization and integration of LSB Hymn **Tune Names** and **Historical/Liturgical Sources** from the workspace TSV files into Hymnody Manager's SQLite database (`hymnody.db`), backend services, and Hymnal Catalog UI.

The TSV input files:
- `LSB Hymn Tracking (blank) - Master List.tsv`: Maps LSB Hymn numbers to Tune names and Source codes.
- `LSB Hymn Tracking (blank) - source.tsv`: Maps Source codes (e.g. `Lu`, `Gerh`) to human-readable meanings (e.g. `Luther`, `Paul Gerhardt`).

Upon completion of the migration, the `.tsv` files will be disposed of, and a Python seed module (`src/lsb_seed_data.py`) will ensure fresh installations on any machine can initialize the complete LSB catalog seamlessly.

---

## 1. Database Schema & Seed Architecture

### Schema Changes (`hymnody.db`)

1. **`sources` Table**:
   ```sql
   CREATE TABLE IF NOT EXISTS sources (
       code TEXT PRIMARY KEY,
       meaning TEXT NOT NULL
   );
   ```

2. **`tunes` Table**:
   ```sql
   CREATE TABLE IF NOT EXISTS tunes (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT NOT NULL UNIQUE
   );
   ```

3. **`hymns` Table Columns**:
   - `tune_id INTEGER REFERENCES tunes(id)`
   - `source_code TEXT REFERENCES sources(code)`
   - `file_path` constraint adjusted to allow `NULL` for unscanned catalog placeholder hymns.

---

## 2. Ingestion, Migration & Scanner Flow

### Seed Module (`src/lsb_seed_data.py`)
A static Python module generated during migration containing the complete dictionary of:
- `SOURCES`: List of `(code, meaning)` tuples.
- `TUNES`: Sorted list of unique tune names.
- `HYMN_CATALOG`: Master list of `(hymn_number, title, season, tune_name, source_code)`.

### Migration Script (`scripts/migrate_tsv_metadata.py`)
1. Parses `source.tsv` and `Master List.tsv`.
2. Generates `src/lsb_seed_data.py`.
3. Runs DDL schema updates on `hymnody.db` (`sources`, `tunes`, `hymns` columns).
4. Seeds `sources` and `tunes` tables.
5. Performs in-place `UPDATE` on existing scanned `hymns` records in `hymnody.db` matching by `hymn_number`, attaching `tune_id` and `source_code` without modifying audio file paths or track metadata.
6. Inserts unscanned LSB catalog placeholder rows (`file_path = NULL`) for missing hymns.
7. Prompts user to safely remove the `.tsv` files after verification.

### Startup Ingestion (`src/database.py` & `src/scanner.py`)
- `init_db()` uses `src/lsb_seed_data.py` to seed `sources`, `tunes`, and full catalog placeholders on fresh database instances.
- `scanner.py` attaches scanned audio track metadata (`file_path`, `disc_number`, `track_number`, etc.) to existing `hymns` catalog records by matching `hymn_number`.

---

## 3. Backend API & Service Layer

- Repository queries (`get_all_hymns`, `get_hymn_by_id`, catalog search) use `LEFT JOIN tunes ON hymns.tune_id = tunes.id LEFT JOIN sources ON hymns.source_code = sources.code`.
- JSON responses for `GET /api/hymns` include `tune_name` and `source_meaning`.
- Query filtering on `GET /api/hymns` matches search terms across `hymn_number`, `title`, `tune_name`, and `source_meaning`.

---

## 4. Frontend & UI Design

### Hymnal Catalog Sidebar (`src/static/app.js` & `index.html`)
- Each hymn item in the catalog list renders:
  - Line 1: `[LSB ###] Hymn Title` (with preview play button).
  - Line 2: `🎵 Tune: <Tune Name> | 📜 Source: <Source Meaning>` (e.g., `🎵 St. Thomas | 📜 Luther`).
  - Missing Audio Badge if `file_path` is null.
- Catalog text search box (`#search-input`) filters by Title, Hymn #, Tune Name, and Source Meaning.

### Service Planner
- Service planner slot cards remain lightweight (no tune/source displayed), as tune and source details are only needed during hymn selection in the catalog sidebar.

---

## 5. Testing & Verification

- `tests/test_tsv_migration.py`: Tests migration script, seed generation, schema alterations, and existing DB updates.
- `tests/test_database.py`: Verifies `init_db()` seeding without `.tsv` files and joined queries.
- `tests/test_api.py`: Verifies API JSON responses and search filtering.
