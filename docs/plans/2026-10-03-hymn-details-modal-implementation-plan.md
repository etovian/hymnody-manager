# Hymn Details & Historical Usage Modal Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provide an interactive modal dialog in the Hymnal Catalog displaying comprehensive hymn metadata, chronological service usage history (dates, liturgical days, settings, slots), and sibling hymns sharing the same tune with preview playback.

**Architecture:** Extend SQLite queries in `src/database.py` with `get_hymn_usage_history` and `get_hymns_sharing_tune`, enrich the `GET /api/hymns/{hymn_id}` endpoint in `src/main.py`, and build a responsive dark-theme modal in `src/static/index.html`, `styles.css`, and `app.js`.

**Tech Stack:** Python 3.11/3.13, FastAPI, SQLite, Vanilla HTML5/CSS/JavaScript, pytest.

---

### Task 1: Database Queries for Hymn Usage History and Same-Tune Hymns

**Files:**
- Modify: `src/database.py`
- Test: `tests/test_database.py`

**Step 1: Write the failing tests in `tests/test_database.py`**
Add tests verifying `get_hymn_usage_history` and `get_hymns_sharing_tune`:
```python
def test_get_hymn_usage_history_and_same_tune(test_db):
    from src.database import (
        save_hymns, get_hymn_usage_history, get_hymns_sharing_tune,
        get_db_connection
    )
    # Setup test hymns with a shared tune
    hymns = [
        {"id": 901, "hymn_number": 901, "title": "Hymn One", "tune_id": 1},
        {"id": 902, "hymn_number": 902, "title": "Hymn Two", "tune_id": 1},
        {"id": 903, "hymn_number": 903, "title": "Hymn Three", "tune_id": 2},
    ]
    save_hymns(hymns, db_path=test_db)

    # Insert mock services and service_items using Hymn One
    with get_db_connection(test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO services (id, service_date, title, liturgical_day, setting_preset)
            VALUES (101, '2026-04-05', 'Easter Day Service', 'The Resurrection of Our Lord', 'DS3')
        """)
        cursor.execute("""
            INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path, is_hymn_slot)
            VALUES (101, 901, 'Hymn One', 'Hymn of the Day', 6, 'mock.m4a', 1)
        """)
        cursor.execute("""
            INSERT INTO services (id, service_date, title, liturgical_day, setting_preset)
            VALUES (102, '2026-05-14', 'Ascension Service', 'The Ascension of Our Lord', 'DS1')
        """)
        cursor.execute("""
            INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path, is_hymn_slot)
            VALUES (102, 901, 'Hymn One', 'Closing Hymn', 13, 'mock.m4a', 1)
        """)
        conn.commit()

    # Verify usage history
    history = get_hymn_usage_history(901, db_path=test_db)
    assert len(history) == 2
    assert history[0]["service_date"] == "2026-05-14"
    assert history[0]["setting_preset"] == "DS1"
    assert history[0]["slot_name"] == "Closing Hymn"
    assert history[1]["service_date"] == "2026-04-05"
    assert history[1]["setting_preset"] == "DS3"

    # Verify same-tune siblings (excluding self)
    siblings = get_hymns_sharing_tune(1, exclude_hymn_id=901, db_path=test_db)
    assert len(siblings) == 1
    assert siblings[0]["id"] == 902
    assert siblings[0]["title"] == "Hymn Two"
```

**Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_database.py -k test_get_hymn_usage_history_and_same_tune -v`
Expected: FAIL with `ImportError: cannot import name 'get_hymn_usage_history'`

**Step 3: Implement functions in `src/database.py`**
Add:
```python
def get_hymn_usage_history(hymn_id, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id AS service_id,
                   s.service_date,
                   s.title AS service_title,
                   s.liturgical_day,
                   s.setting_preset,
                   si.slot_name,
                   si.sequence_order
            FROM service_items si
            JOIN services s ON si.service_id = s.id
            WHERE si.hymn_id = ?
            ORDER BY s.service_date DESC, s.id DESC, si.sequence_order ASC
        """, (hymn_id,))
        return [dict(r) for r in cursor.fetchall()]


def get_hymns_sharing_tune(tune_id, exclude_hymn_id=None, db_path=DEFAULT_DB_PATH):
    if not tune_id:
        return []
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        sql = """
            SELECT h.id, h.hymn_number, h.title, h.liturgical_season,
                   h.disc_number, h.track_number, h.file_path,
                   t.name AS tune_name, s.meaning AS source_meaning
            FROM hymns h
            LEFT JOIN tunes t ON h.tune_id = t.id
            LEFT JOIN sources s ON h.source_code = s.code
            WHERE h.tune_id = ?
        """
        params = [tune_id]
        if exclude_hymn_id is not None:
            sql += " AND h.id != ?"
            params.append(exclude_hymn_id)
        sql += """
            ORDER BY CASE WHEN h.hymn_number IS NOT NULL THEN 0 ELSE 1 END ASC,
                     h.hymn_number ASC, h.title ASC
        """
        cursor.execute(sql, params)
        return [dict(r) for r in cursor.fetchall()]
```

**Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_database.py -k test_get_hymn_usage_history_and_same_tune -v`
Expected: PASS

**Step 5: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/database.py', 'tests/test_database.py']); subprocess.run(['git', 'commit', '-m', 'feat(db): add get_hymn_usage_history and get_hymns_sharing_tune'])"
```

---

### Task 2: API Endpoint Enhancement for Enriched Hymn Details

**Files:**
- Modify: `src/main.py`
- Test: `tests/test_api.py`

**Step 1: Write failing test in `tests/test_api.py`**
Add test verifying `GET /api/hymns/{hymn_id}` contains `usage_history` and `same_tune_hymns`:
```python
def test_get_hymn_enriched_details(client):
    # Fetch a hymn from existing catalog
    res = client.get("/api/hymns")
    assert res.status_code == 200
    hymns = res.json()
    assert len(hymns) > 0
    test_hymn = hymns[0]

    res = client.get(f"/api/hymns/{test_hymn['id']}")
    assert res.status_code == 200
    data = res.json()
    assert "usage_history" in data
    assert isinstance(data["usage_history"], list)
    assert "same_tune_hymns" in data
    assert isinstance(data["same_tune_hymns"], list)
```

**Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_api.py -k test_get_hymn_enriched_details -v`
Expected: FAIL with `KeyError: 'usage_history'` or `assert 'usage_history' in data` failure.

**Step 3: Update `src/main.py`**
Import `get_hymn_usage_history` and `get_hymns_sharing_tune` from `src.database`.
Update `api_get_hymn`:
```python
@app.get("/api/hymns/{hymn_id}")
def api_get_hymn(hymn_id: int):
    db_path = get_db_path()
    hymn = get_hymn_by_id(hymn_id, db_path=db_path)
    if not hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    hymn["usage_history"] = get_hymn_usage_history(hymn_id, db_path=db_path)
    hymn["same_tune_hymns"] = (
        get_hymns_sharing_tune(hymn["tune_id"], exclude_hymn_id=hymn_id, db_path=db_path)
        if hymn.get("tune_id") else []
    )
    return hymn
```

**Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_api.py -k test_get_hymn_enriched_details -v`
Expected: PASS

**Step 5: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/main.py', 'tests/test_api.py']); subprocess.run(['git', 'commit', '-m', 'feat(api): enrich GET /api/hymns/{hymn_id} with usage history and same tune hymns'])"
```

---

### Task 3: Modal HTML & CSS in Frontend

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`

**Step 1: Add Modal Markup to `src/static/index.html`**
Add `#hymn-details-modal`:
```html
<!-- HYMN DETAILS MODAL -->
<div id="hymn-details-modal" class="modal-backdrop hidden" onclick="if(event.target === this) closeHymnDetailsModal()">
  <div class="modal-card" style="max-width: 800px; width: 95%; max-height: 90vh; display: flex; flex-direction: column;">
    <div class="modal-header flex-between" style="border-bottom: 1px solid #334155; padding-bottom: 12px;">
      <div>
        <h3 id="modal-hymn-title" style="font-size: 1.2rem; font-weight: 700; color: #f8fafc;">Hymn Details</h3>
        <p id="modal-hymn-subtitle" class="subtitle" style="font-size: 0.8rem; color: #94a3b8; margin: 0;"></p>
      </div>
      <button class="btn-close" onclick="closeHymnDetailsModal()">✕</button>
    </div>
    <div class="modal-body" style="overflow-y: auto; padding: 16px 4px; display: flex; flex-direction: column; gap: 16px;">
      <!-- Metadata Bar -->
      <div id="modal-metadata-bar" style="display: flex; gap: 8px; flex-wrap: wrap; background: #0f172a; padding: 10px 12px; border-radius: 8px; border: 1px solid #334155;">
        <!-- Dynamically injected badges -->
      </div>

      <!-- Usage History Section -->
      <div>
        <h4 id="modal-history-heading" style="font-size: 0.95rem; font-weight: 700; color: #e2e8f0; margin-bottom: 8px;">Previous Service Usage</h4>
        <div id="modal-history-container" style="background: #0f172a; border-radius: 8px; border: 1px solid #334155; overflow: hidden;">
          <!-- Dynamically injected table or empty state -->
        </div>
      </div>

      <!-- Sibling Hymns Section -->
      <div>
        <h4 id="modal-tune-heading" style="font-size: 0.95rem; font-weight: 700; color: #e2e8f0; margin-bottom: 8px;">Other Hymns Sharing This Tune</h4>
        <div id="modal-siblings-container" style="display: flex; flex-direction: column; gap: 8px;">
          <!-- Dynamically injected sibling cards or empty state -->
        </div>
      </div>
    </div>
  </div>
</div>
```

**Step 2: Add CSS rules to `src/static/styles.css`**
Add styling for the history table, sibling cards, and info buttons:
```css
/* Hymn Details Modal Specifics */
.hymn-history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  text-align: left;
}
.hymn-history-table th {
  background: #1e293b;
  color: #94a3b8;
  font-weight: 600;
  padding: 8px 12px;
  border-bottom: 1px solid #334155;
}
.hymn-history-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #1e293b;
  color: #f1f5f9;
}
.hymn-history-table tr:last-child td {
  border-bottom: none;
}
.sibling-hymn-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.sibling-hymn-card:hover {
  background: #1e293b;
  border-color: #475569;
}
.btn-icon-info {
  background: #1e293b;
  color: #94a3b8;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-icon-info:hover {
  background: #334155;
  color: #38bdf8;
  border-color: #38bdf8;
}
```

**Step 3: Run existing validator test**
Run: `python -m pytest tests/test_html_validator.py -v`
Expected: PASS

**Step 4: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/styles.css']); subprocess.run(['git', 'commit', '-m', 'feat(ui): add hymn details modal markup and css styles'])"
```

---

### Task 4: Frontend JavaScript Logic & Interaction

**Files:**
- Modify: `src/static/app.js`

**Step 1: Add Info Button to `renderHymnList` and title click listener**
In `renderHymnList(hymns)`:
```javascript
item.innerHTML = `
  <div style="display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0;">
    <span class="drag-handle">⋮⋮</span>
    <div style="cursor: pointer;" onclick="openHymnDetailsModal(${h.id})">
      <span class="badge" style="margin-right: 6px;">${numTag}</span>
      <span style="font-weight: 500;">${escapeHtml(h.title)}</span>
      <div class="subtitle">${discTrackSubtitle}</div>
      <div class="subtitle">🎵 Tune: ${escapeHtml(h.tune_name || 'Unknown')} | 📜 Source: ${escapeHtml(h.source_meaning || 'Unknown')}</div>
    </div>
  </div>
  <div style="display: flex; align-items: center; gap: 6px;">
    <button class="btn btn-primary" onclick="event.stopPropagation(); playCatalogHymn(${h.id})">▶ Play</button>
    <button class="btn-icon-info" onclick="event.stopPropagation(); openHymnDetailsModal(${h.id})" title="View hymn usage history and shared tunes">ℹ️ Info</button>
  </div>
`;
```

**Step 2: Implement `openHymnDetailsModal` and `closeHymnDetailsModal` in `src/static/app.js`**
- Show loading state in modal.
- Fetch `/api/hymns/${hymnId}`.
- Render Title, Badges (Tune, Season, Source, Audio Disc/Track).
- Render History table (Date, Liturgical Day, Setting, Service Title, Slot Name) or empty state.
- Render Sibling hymns (card with title, play preview button, click card navigates `openHymnDetailsModal(sibling.id)`).
- Add Escape key listener to close modal.

**Step 3: Verify all unit and integration tests pass**
Run: `python -m pytest tests/ -v`
Expected: 100% PASS

**Step 4: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat(ui): implement hymn details modal rendering, navigation, and playback'])"
```

---

### Task 5: End-to-End & Integration Tests

**Files:**
- Modify: `tests/test_e2e.py`

**Step 1: Add End-to-End tests verifying modal flow**
In `tests/test_e2e.py`:
- Test that modal elements and classes exist in `index.html`.
- Test that API returns enriched data with populated service items.
- Test that sibling hymns share matching `tune_id`.
- Test that audio streaming endpoint works when triggered from modal.

**Step 2: Run pytest across the entire suite**
Run: `python -m pytest -v`
Expected: All tests pass.

**Step 3: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'test(e2e): add integration tests for hymn details modal and tune sharing'])"
```
