# Worship Planning Features Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement worship date selection, Services Explorer modal, dual-zone drag & drop (insert vs replace), database-backed editable templates with corrected LCMS DS3 ordinaries, and historical service persistence in Hymnody Manager.

**Architecture:** Extend SQLite database schema (`service_templates`, `template_items`, `services` columns) in `database.py`; implement preset seeding, template CRUD, and dynamic rubric verification in `services.py`; add REST API endpoints in `main.py`; and update vanilla HTML5/CSS3/JS frontend components in `static/`.

**Tech Stack:** Python 3.11, FastAPI, SQLite3, HTML5, CSS3, Vanilla JS, Pytest.

---

### Task 1: Database Schema Extension & Template Seeding (`src/database.py`)

**Files:**
- Modify: `src/database.py`
- Test: `tests/test_database.py`

**Step 1: Write the failing test**
Add `test_template_tables_and_service_columns` in `tests/test_database.py`:
```python
def test_template_tables_and_service_columns(tmp_path):
    db_path = str(tmp_path / "test_templates_schema.db")
    init_db(db_path)
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_templates'")
        assert cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='template_items'")
        assert cursor.fetchone() is not None
        
        cursor.execute("PRAGMA table_info(services)")
        cols = [col['name'] for col in cursor.fetchall()]
        assert 'liturgical_day' in cols
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_database.py -v`
Expected: FAIL with missing tables / columns.

**Step 3: Implement minimal code in `src/database.py`**
Update `init_db()` in `src/database.py` to create `service_templates` and `template_items` tables, and ensure `services` has `liturgical_day`:
```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        is_builtin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS template_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        slot_name TEXT NOT NULL,
        match_term TEXT,
        item_title TEXT NOT NULL,
        sequence_order INTEGER NOT NULL,
        is_hymn_slot INTEGER DEFAULT 0,
        FOREIGN KEY (template_id) REFERENCES service_templates(id) ON DELETE CASCADE
    );
""")
```
Also execute migration logic to add `liturgical_day` to `services` if missing.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_database.py -v`
Expected: PASS.

---

### Task 2: Preset Database Seeding, Template CRUD & DS3 Ordinary Corrections (`src/services.py`)

**Files:**
- Modify: `src/services.py`
- Test: `tests/test_services.py`

**Step 1: Write the failing test**
Add `test_seed_templates_and_corrected_ds3` in `tests/test_services.py`:
```python
def test_seed_templates_and_corrected_ds3(tmp_path):
    db_path = str(tmp_path / "test_templates.db")
    init_db(db_path)
    seed_templates_if_empty(db_path)
    
    templates = list_templates(db_path)
    assert len(templates) >= 7
    
    ds3 = get_template_by_name("DS3", db_path)
    assert ds3 is not None
    
    items = ds3['items']
    salutation = next((i for i in items if "Salutation" in i['item_title'] or "Salutation" in i['slot_name']), None)
    assert salutation is not None
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_services.py::test_seed_templates_and_corrected_ds3 -v`
Expected: FAIL (`seed_templates_if_empty` / `list_templates` not defined).

**Step 3: Write implementation in `src/services.py`**
Implement `seed_templates_if_empty()`, `list_templates()`, `get_template_by_name()`, `get_template_by_id()`, `save_template()`, `delete_template()`.
Update `PRESETS` dictionary to seed complete LCMS templates including DS3's Salutation and Collect Amen. Update `create_service_from_preset` to load from database templates.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_services.py -v`
Expected: PASS.

---

### Task 3: REST API Endpoints for Templates & Services Explorer (`src/main.py`)

**Files:**
- Modify: `src/main.py`
- Test: `tests/test_api.py`

**Step 1: Write the failing test**
Add `test_template_and_service_explorer_api` in `tests/test_api.py`:
```python
def test_template_and_service_explorer_api(tmp_path):
    # Test GET /api/templates
    # Test POST /api/templates
    # Test PUT /api/services/{id}/metadata (updating service_date and liturgical_day)
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_api.py -v`
Expected: FAIL (endpoints return 404 or missing).

**Step 3: Write implementation in `src/main.py`**
Add:
- `GET /api/templates`
- `GET /api/templates/{id}`
- `POST /api/templates`
- `PUT /api/templates/{id}`
- `DELETE /api/templates/{id}`
- `PUT /api/services/{id}/metadata` (updates `service_date`, `liturgical_day`, `title`, `notes`)
- `GET /api/analytics/hymn-usage`

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_api.py -v`
Expected: PASS.

---

### Task 4: Worship Date Picker & Services Explorer UI (`src/static/index.html`, `src/static/app.js`, `src/static/styles.css`)

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`
- Modify: `src/static/app.js`

**Step 1: HTML & CSS Updates**
- Update right panel header in `index.html`: replace static date display with `<input type="date" id="service-date-input">` and `<input type="text" id="liturgical-day-input">`.
- Add **Services Explorer** button.
- Add Services Explorer Modal markup in `index.html`.
- Add styling for modal dialogs and filter tabs in `styles.css`.

**Step 2: JS Logic in `app.js`**
- Bind change listener on date picker and `liturgical_day` input to sync metadata with backend API (`PUT /api/services/{id}/metadata`).
- Implement `openServicesExplorer()`, `fetchAndRenderSavedServices()`, `loadService(id)`, `duplicateService(id)`, `deleteService(id)`.

**Step 3: Manual Verification**
Open browser, change service date, test Services Explorer modal, load past services, verify persistence across refreshes.

---

### Task 5: Dual-Zone Drag-and-Drop (Insert vs Replace) (`src/static/styles.css`, `src/static/app.js`)

**Files:**
- Modify: `src/static/styles.css`
- Modify: `src/static/app.js`

**Step 1: CSS Indicators in `styles.css`**
- Add `.drag-insert-above` (blue top border), `.drag-insert-below` (blue bottom border), and `.drag-replace` (highlight card outline).

**Step 2: Dual-Zone Logic in `app.js`**
- Update `onDragOver(e)`: calculate `const rect = e.currentTarget.getBoundingClientRect()`, `const y = e.clientY - rect.top`, `const pct = y / rect.height`.
- If `pct < 0.25`: set drag mode `insert-above`.
- If `pct > 0.75`: set drag mode `insert-below`.
- Otherwise: set drag mode `replace`.
- Update `onHymnDrop(e, targetIndex)`:
  - If `replace`: call `assignHymnToSlot(hymnId, targetIndex)`.
  - If `insert-above` / `insert-below`: call `insertHymnAtSlot(hymnId, targetIndex)`.

**Step 3: Manual Verification**
Test dragging catalog hymns to top/bottom of a slot to insert, middle of a slot to replace, and reordering within plan.

---

### Task 6: Template Editor Modal UI (`src/static/index.html`, `src/static/app.js`, `src/static/styles.css`)

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/app.js`
- Modify: `src/static/styles.css`

**Step 1: HTML & CSS Updates**
- Add **Manage Templates** button in header menu.
- Add Template Editor Modal markup in `index.html` (template list, slot reorder/edit table, add slot button, save button).

**Step 2: JS Logic in `app.js`**
- Implement `openTemplateEditor()`, `renderTemplateSlots()`, `addTemplateSlot()`, `saveTemplate()`.

**Step 3: Manual Verification**
Open Template Editor, edit DS3 to inspect ordinaries, add custom template, save and verify available in preset selector.

---

### Task 7: Comprehensive Integration & Verification

**Files:**
- Test: `tests/test_e2e.py`

**Step 1: Run full test suite**
Run: `pytest -v`
Expected: ALL PASS.

**Step 2: End-to-End Application Check**
Start dev server: `uvicorn src.main:app --reload`
Verify date picker, Services Explorer, dual-zone drag & drop, template editing, and zip exports.
