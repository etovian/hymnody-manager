# LSB Hymn Tune & Historical Source Tracking Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Normalize and integrate LSB Hymn Tune names and Historical Source metadata from TSV files into SQLite (`hymnody.db`), backend services, and the Hymnal Catalog UI, enabling `.tsv` file disposal while preserving fresh machine initialization via a generated Python seed module.

**Architecture:** A migration script parses `.tsv` files to create `src/lsb_seed_data.py`, updates `hymnody.db` with `sources` and `tunes` tables, and adds `tune_id` and `source_code` columns to `hymns`. Joined queries supply `tune_name` and `source_meaning` to the REST API and the frontend catalog UI.

**Tech Stack:** Python 3.13, SQLite, FastAPI, HTML5/CSS/Vanilla JS, pytest.

---

### Task 1: Seed Data Generator & TSV Migration Script

**Files:**
- Create: `scripts/migrate_tsv_metadata.py`
- Create: `src/lsb_seed_data.py`
- Create: `tests/test_tsv_migration.py`

**Step 1: Write the failing test**

```python
# tests/test_tsv_migration.py
import pytest
import os
import sqlite3
from scripts.migrate_tsv_metadata import parse_tsvs, generate_seed_data

def test_parse_tsvs_and_generate_seed_data(tmp_path):
    sources, tunes, catalog = parse_tsvs(
        "LSB Hymn Tracking (blank) - source.tsv",
        "LSB Hymn Tracking (blank) - Master List.tsv"
    )
    assert len(sources) > 30
    assert any(code == 'Lu' and meaning == 'Luther' for code, meaning in sources)
    assert "St. Thomas" in tunes
    
    # Check catalog entry for Hymn 331
    h331 = next((item for item in catalog if item['hymn_number'] == 331), None)
    assert h331 is not None
    assert h331['title'] == "The Advent of Our King"
    assert h331['tune_name'] == "St. Thomas"
    assert h331['source_code'] == "RC1900"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_tsv_migration.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.migrate_tsv_metadata'`

**Step 3: Write minimal implementation**

Create `scripts/migrate_tsv_metadata.py` to parse TSV files, generate `src/lsb_seed_data.py`, update `hymnody.db`, and support verification and cleanup.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_tsv_migration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'scripts/migrate_tsv_metadata.py', 'src/lsb_seed_data.py', 'tests/test_tsv_migration.py']); subprocess.run(['git', 'commit', '-m', 'feat: add TSV parser and seed generator script'])"
```

---

### Task 2: Database Schema & Seeding Repository Updates

**Files:**
- Modify: `src/database.py`
- Modify: `tests/test_database.py`

**Step 1: Write the failing test**

```python
# In tests/test_database.py
def test_init_db_seeds_sources_and_tunes(tmp_path):
    db_path = str(tmp_path / "test_hymnody.db")
    init_db(db_path)
    
    with get_db_connection(db_path) as conn:
        sources = conn.execute("SELECT * FROM sources WHERE code = 'Lu'").fetchone()
        assert sources is not None
        assert sources['meaning'] == 'Luther'
        
        tunes = conn.execute("SELECT * FROM tunes WHERE name = 'St. Thomas'").fetchone()
        assert tunes is not None

        # Verify joined hymn query
        hymns = get_all_hymns(db_path)
        assert len(hymns) > 0
        h331 = next((h for h in hymns if h.get('hymn_number') == 331), None)
        assert h331 is not None
        assert h331.get('tune_name') == "St. Thomas"
        assert h331.get('source_meaning') == "Roman Catholic hymns to 1900"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_database.py::test_init_db_seeds_sources_and_tunes -v`
Expected: FAIL with `sqlite3.OperationalError: no such table: sources`

**Step 3: Write minimal implementation**

Modify `src/database.py`:
- In `init_db()`: Create `sources` and `tunes` tables if not exists. Add `tune_id` and `source_code` columns to `hymns` if missing. Seed `sources`, `tunes`, and catalog placeholders from `src/lsb_seed_data.py`.
- In `get_all_hymns()` and `get_hymn_by_id()`: Add `LEFT JOIN tunes ON hymns.tune_id = tunes.id LEFT JOIN sources ON hymns.source_code = sources.code`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_database.py -v`
Expected: PASS

**Step 5: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/database.py', 'tests/test_database.py']); subprocess.run(['git', 'commit', '-m', 'feat: update database schema with sources, tunes, and joined queries'])"
```

---

### Task 3: Scanner Catalog Association

**Files:**
- Modify: `src/scanner.py`
- Modify: `tests/test_scanner.py`

**Step 1: Write the failing test**

```python
# In tests/test_scanner.py
def test_scan_associates_audio_with_catalog(tmp_path):
    db_path = str(tmp_path / "test_hymnody.db")
    init_db(db_path)
    # Simulate scanning an audio file for Hymn 331
    # Verify that file_path, disc_number, track_number are attached to the existing hymn 331 record
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scanner.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `src/scanner.py` to match scanned files by `hymn_number` against existing catalog rows in `hymns` and update `file_path`, `disc_number`, `track_number`, `album`, `artist`, `year`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_scanner.py -v`
Expected: PASS

**Step 5: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/scanner.py', 'tests/test_scanner.py']); subprocess.run(['git', 'commit', '-m', 'feat: update scanner to attach audio paths to catalog hymns'])"
```

---

### Task 4: API Endpoint & Search Filtering

**Files:**
- Modify: `src/main.py`
- Modify: `tests/test_api.py`

**Step 1: Write the failing test**

```python
# In tests/test_api.py
def test_get_hymns_returns_tune_and_source_and_filters():
    response = client.get("/api/hymns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    first = data[0]
    assert "tune_name" in first
    assert "source_meaning" in first
    
    # Test filtering by tune name
    res_tune = client.get("/api/hymns?q=St.%20Thomas")
    assert res_tune.status_code == 200
    assert any("St. Thomas" in (h.get("tune_name") or "") for h in res_tune.json())
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py::test_get_hymns_returns_tune_and_source_and_filters -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `src/main.py`: Update `/api/hymns` endpoint to return `tune_name` and `source_meaning` and update search filtering to check `tune_name` and `source_meaning`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/main.py', 'tests/test_api.py']); subprocess.run(['git', 'commit', '-m', 'feat: include tune_name and source_meaning in API responses and search'])"
```

---

### Task 5: Hymnal Catalog UI Updates

**Files:**
- Modify: `src/static/app.js`
- Modify: `src/static/index.html`

**Step 1: Write the failing test / HTML validation check**

Verify in `tests/test_html_validator.py` or JS catalog rendering that tune name and source meaning are formatted in catalog card items.

**Step 2: Write implementation**

Modify `src/static/app.js`:
- In catalog item rendering function, append secondary metadata line: `🎵 Tune: ${hymn.tune_name || 'Unknown'} | 📜 Source: ${hymn.source_meaning || 'Unknown'}`.
- Update client-side catalog search filtering to match `hymn.tune_name` and `hymn.source_meaning`.

**Step 3: Manual & Automated UI Verification**

Run `python -m pytest tests/test_html_validator.py -v` to ensure HTML markup validity.

**Step 4: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js', 'src/static/index.html']); subprocess.run(['git', 'commit', '-m', 'feat: render tune name and source meaning in hymnal catalog UI'])"
```

---

### Task 6: Migration Execution & TSV Cleanup

**Files:**
- Run: `scripts/migrate_tsv_metadata.py`
- Delete: `LSB Hymn Tracking (blank) - Master List.tsv`
- Delete: `LSB Hymn Tracking (blank) - source.tsv`

**Step 1: Execute Migration & Verification**

Run: `python scripts/migrate_tsv_metadata.py`
Expected: Database migrated, `src/lsb_seed_data.py` generated, `.tsv` files disposed of.

**Step 2: Run full test suite**

Run: `python -m pytest -v`
Expected: All 92+ tests PASS.

**Step 3: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/lsb_seed_data.py', 'hymnody.db']); subprocess.run(['git', 'rm', 'LSB Hymn Tracking (blank) - Master List.tsv', 'LSB Hymn Tracking (blank) - source.tsv']); subprocess.run(['git', 'commit', '-m', 'chore: complete TSV metadata migration and cleanup'])"
```
