# Dual-Tab Hymnal Catalog & Liturgical Categorization Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the Hymnal Catalog into a dual-tab UI (**🎵 Hymns** vs **📜 Liturgy**) with alphabetized dropdown category filters (Communion, Baptism, Confession, Matins, Vespers, DS1-DS5, etc.), guaranteed sorting by Disc ASC & Track ASC, and path normalization to eliminate duplicate tracks caused by Windows drive letter casing.

**Architecture:** Extend `parse_hymn_file()` in `scanner.py` to classify Disc 30/31 office settings and LSB sacramental hymn ranges (`Communion`, `Baptism`, `Confession`). Add path normalization (`normalize_path`) and database deduplication migration to `database.py`. Update `search_hymns()` in `database.py` and `api_get_hymns()` in `main.py` to filter by `category_type` (`'hymn'` vs `'liturgy'`) and enforce `ORDER BY disc_number ASC, track_number ASC`. Update `index.html` and `app.js` with tab controls and alphabetized dropdown menus.

**Tech Stack:** Python 3.11, FastAPI, SQLite3, HTML5/CSS3, Vanilla JS, Pytest.

---

### Task 1: Scanner Classification & Metadata Parsing

**Files:**
- Modify: `src/scanner.py:113-143`
- Test: `tests/test_scanner.py`

*(Completed & Verified)*

---

### Task 2: Database Query & Search Alias Expansion

**Files:**
- Modify: `src/database.py:104-131`
- Test: `tests/test_database.py`

*(Completed & Verified)*

---

### Task 3: REST API Endpoint Updates

**Files:**
- Modify: `src/main.py:47-50`
- Test: `tests/test_api.py`

*(Completed & Verified)*

---

### Task 4: Frontend Web UI (Dual-Tab Hymnal Catalog)

**Files:**
- Modify: `src/static/index.html:30-53`
- Modify: `src/static/app.js:3-80`
- Modify: `src/static/styles.css`
- Test: `tests/test_e2e.py`

*(Completed & Verified)*

---

### Task 5: Path Normalization & Database Duplicate Cleanup

**Files:**
- Modify: `src/scanner.py`
- Modify: `src/database.py`
- Test: `tests/test_database.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_database.py
def test_path_normalization_and_deduplication(tmp_path):
    from src.database import init_db, save_hymns, search_hymns, normalize_path
    db_path = str(tmp_path / "dedup_test.db")
    init_db(db_path)
    
    # Save dummy tracks with different path casing for the same physical file
    p1 = r"c:\dev\IdeaProjects\hymnody-manager\music\30-06 DS1 - Kyrie_ Amen.m4a"
    p2 = r"C:\dev\IdeaProjects\hymnody-manager\music\30-06 DS1 - Kyrie_ Amen.m4a"
    
    save_hymns([
        {'hymn_number': None, 'title': 'DS1 - Kyrie_ Amen', 'disc_number': 30, 'track_number': 6, 'file_path': p1, 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Kyrie_ Amen', 'disc_number': 30, 'track_number': 6, 'file_path': p2, 'liturgical_season': 'DS1'}
    ], db_path)

    results = search_hymns(disc=30, db_path=db_path)
    assert len(results) == 1, "Duplicate paths with different drive casing should be deduplicated"
    assert results[0]['file_path'] == normalize_path(p1)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_database.py::test_path_normalization_and_deduplication -v`

**Step 3: Implement minimal code in `src/scanner.py` and `src/database.py`**

In `src/scanner.py` and `src/database.py`, add `normalize_path(path)`:
```python
def normalize_path(path):
    if not path:
        return ""
    norm = os.path.abspath(path)
    if len(norm) >= 2 and norm[1] == ':':
        norm = norm[0].upper() + norm[1:]
    return norm
```

In `src/database.py`, update `init_db()` and `save_hymns()` to normalize `file_path` before inserting and run a deduplication query:
```python
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hymns WHERE id NOT IN (SELECT MAX(id) FROM hymns GROUP BY LOWER(file_path))")
        conn.commit()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_database.py -v`

**Step 5: Commit via Python subprocess**

```bash
python -c "import subprocess; subprocess.run(['git', 'commit', '-am', 'fix: normalize file paths and deduplicate hymns database entries'])"
```

---

### Task 6: Alphabetized Dropdown Filters & Enforced Disc/Track Sorting

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/app.js`
- Modify: `src/database.py`
- Test: `tests/test_e2e.py`

**Step 1: Write failing test in `tests/test_e2e.py`**

```python
def test_alphabetized_filters_and_sorting(tmp_path):
    from src.database import init_db, save_hymns, search_hymns
    db_path = str(tmp_path / "sort_test.db")
    init_db(db_path)
    save_hymns([
        {'hymn_number': 332, 'title': 'Savior of the nations', 'disc_number': 1, 'track_number': 2, 'file_path': r'c:\m\1-02.m4a', 'liturgical_season': 'Advent'},
        {'hymn_number': 331, 'title': 'The advent of our King', 'disc_number': 1, 'track_number': 1, 'file_path': r'c:\m\1-01.m4a', 'liturgical_season': 'Advent'}
    ], db_path)
    
    results = search_hymns(db_path=db_path)
    assert results[0]['track_number'] == 1
    assert results[1]['track_number'] == 2
```

**Step 2: Run test to verify**

Run: `pytest tests/test_e2e.py::test_alphabetized_filters_and_sorting -v`

**Step 3: Implement frontend dropdowns & JS logic**

In `src/static/index.html`:
Replace `#season-filters` pills with a styled `<select id="season-select" class="dropdown-filter" onchange="filterSeason(this.value)">`.

In `src/static/app.js`:
Define alphabetized dropdown lists:
```javascript
const HYMN_SEASONS = [
  { label: 'All Hymns', value: '' },
  { label: 'Advent', value: 'Advent' },
  { label: 'Baptism', value: 'Baptism' },
  { label: 'Christmas', value: 'Christmas' },
  { label: 'Communion', value: 'Communion' },
  { label: 'Confession', value: 'Confession' },
  { label: 'Easter', value: 'Easter' },
  { label: 'Epiphany', value: 'Epiphany' },
  { label: 'General', value: 'General' },
  { label: 'Lent', value: 'Lent' },
  { label: 'Pentecost', value: 'Pentecost' },
  { label: 'Praise', value: 'Praise' },
  { label: 'Trust & Comfort', value: 'Trust & Comfort' }
];

const LITURGY_SERVICES = [
  { label: 'All Services', value: '' },
  { label: 'Compline', value: 'Compline' },
  { label: 'DS1', value: 'DS1' },
  { label: 'DS2', value: 'DS2' },
  { label: 'DS3', value: 'DS3' },
  { label: 'DS4', value: 'DS4' },
  { label: 'DS5', value: 'DS5' },
  { label: 'Evening Prayer', value: 'Evening Prayer' },
  { label: 'Matins', value: 'Matins' },
  { label: 'Morning Prayer', value: 'Morning Prayer' },
  { label: 'Psalm Tones', value: 'Psalm Tones' },
  { label: 'Vespers', value: 'Vespers' }
];
```

Implement `renderFilterDropdown()` to populate `#season-select` options cleanly based on active tab (`HYMN_SEASONS` vs `LITURGY_SERVICES`).

**Step 4: Run full pytest suite**

Run: `pytest -v`

**Step 5: Commit via Python subprocess**

```bash
python -c "import subprocess; subprocess.run(['git', 'commit', '-am', 'feat: update catalog UI to alphabetized dropdown filters and enforce sorting'])"
```
