# Hymn Lyrics Display and Editing Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to view, edit/paste, save, and 1-click copy hymn lyrics inside the Hymn Details Modal.

**Architecture:** Add a `lyrics TEXT` column to the `hymns` SQLite table with automatic startup migration, expose it via REST endpoints (`GET /api/hymns/{id}`, `PUT /api/hymns/{id}/lyrics`), and implement a tabbed interface in the Hymn Details Modal with Read Mode, Edit Mode, Empty State, and Clipboard API integration.

**Tech Stack:** Python 3.11+, SQLite, FastAPI, Pydantic, Vanilla HTML5/CSS/JavaScript, Pytest.

---

### Task 1: Database Migration & Persistence for Hymn Lyrics

**Files:**
- Modify: `src/database.py`
- Test: `tests/test_database.py`

**Step 1: Write the failing test**

In `tests/test_database.py`, add `test_hymn_lyrics_migration_and_update`:

```python
def test_hymn_lyrics_migration_and_update(tmp_path):
    from src.database import init_db, save_hymns, get_hymn_by_id, update_hymn_lyrics
    db_path = str(tmp_path / "lyrics_test.db")
    init_db(db_path)

    # Insert a hymn
    save_hymns([{
        'hymn_number': 331,
        'title': 'The advent of our King',
        'disc_number': 1,
        'track_number': 1,
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'file_path': 'dummy/path/1-01.m4a',
        'liturgical_season': 'Advent'
    }], db_path)

    hymn = get_hymn_by_id(1, db_path=db_path)
    assert hymn is not None
    assert 'lyrics' in hymn
    assert hymn['lyrics'] is None

    # Update lyrics
    lyrics_text = "1. The advent of our King\nOur prayers must now employ,\nAnd we must hymns of welcome sing\nIn strains of holy joy."
    success = update_hymn_lyrics(1, lyrics_text, db_path=db_path)
    assert success is True

    # Retrieve and verify
    updated = get_hymn_by_id(1, db_path=db_path)
    assert updated['lyrics'] == lyrics_text

    # Clear lyrics (set to None)
    success = update_hymn_lyrics(1, None, db_path=db_path)
    assert success is True
    cleared = get_hymn_by_id(1, db_path=db_path)
    assert cleared['lyrics'] is None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_database.py::test_hymn_lyrics_migration_and_update -v`
Expected: FAIL with `ImportError: cannot import name 'update_hymn_lyrics'` or missing column.

**Step 3: Write minimal implementation**

In `src/database.py`:
1. In `init_db()`:
   Check `hymn_col_names`:
   ```python
   if 'lyrics' not in hymn_col_names:
       cursor.execute("ALTER TABLE hymns ADD COLUMN lyrics TEXT")
   ```
2. Define `update_hymn_lyrics`:
   ```python
   def update_hymn_lyrics(hymn_id: int, lyrics: str | None, db_path=DEFAULT_DB_PATH) -> bool:
       with get_db_connection(db_path) as conn:
           cursor = conn.cursor()
           cursor.execute("UPDATE hymns SET lyrics = ? WHERE id = ?", (lyrics, hymn_id))
           conn.commit()
           return cursor.rowcount > 0
   ```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_database.py::test_hymn_lyrics_migration_and_update -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/database.py tests/test_database.py
git commit -m "feat(db): add lyrics column migration and update_hymn_lyrics helper"
```

---

### Task 2: API Endpoints for Hymn Lyrics

**Files:**
- Modify: `src/main.py`
- Test: `tests/test_api.py`

**Step 1: Write the failing test**

In `tests/test_api.py`, add `test_lyrics_api_endpoints`:

```python
def test_lyrics_api_endpoints(tmp_path):
    from src.database import init_db, save_hymns
    db_path = str(tmp_path / "lyrics_api_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)

    save_hymns([{
        'hymn_number': 331,
        'title': 'The advent of our King',
        'disc_number': 1,
        'track_number': 1,
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'file_path': 'sample.m4a',
        'liturgical_season': 'Advent'
    }], db_path)

    # 1. GET hymn should include lyrics (null initially)
    res = client.get("/api/hymns/1")
    assert res.status_code == 200
    assert "lyrics" in res.json()
    assert res.json()["lyrics"] is None

    # 2. PUT hymn lyrics
    lyrics_content = "1. The advent of our King\n\n2. The everlasting Son"
    put_res = client.put("/api/hymns/1/lyrics", json={"lyrics": lyrics_content})
    assert put_res.status_code == 200
    body = put_res.json()
    assert body["status"] == "success"
    assert body["hymn"]["lyrics"] == lyrics_content

    # 3. GET again to ensure persistence
    res2 = client.get("/api/hymns/1")
    assert res2.status_code == 200
    assert res2.json()["lyrics"] == lyrics_content

    # 4. Clear lyrics with whitespace/empty
    clear_res = client.put("/api/hymns/1/lyrics", json={"lyrics": "   "})
    assert clear_res.status_code == 200
    assert clear_res.json()["hymn"]["lyrics"] is None

    # 5. Non-existent hymn should 404
    bad_res = client.put("/api/hymns/99999/lyrics", json={"lyrics": "Hello"})
    assert bad_res.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py::test_lyrics_api_endpoints -v`
Expected: FAIL with `405 Method Not Allowed` or `404 Not Found`.

**Step 3: Write minimal implementation**

In `src/main.py`:
1. Import `update_hymn_lyrics` from `src.database`.
2. Add Pydantic model:
   ```python
   class HymnLyricsUpdate(BaseModel):
       lyrics: Optional[str] = None
   ```
3. Add endpoint:
   ```python
   @app.put("/api/hymns/{hymn_id}/lyrics")
   def api_update_hymn_lyrics(hymn_id: int, payload: HymnLyricsUpdate):
       db_path = get_db_path()
       hymn = get_hymn_by_id(hymn_id, db_path=db_path)
       if not hymn:
           raise HTTPException(status_code=404, detail="Hymn not found")
       cleaned = payload.lyrics.strip() if payload.lyrics and payload.lyrics.strip() else None
       update_hymn_lyrics(hymn_id, cleaned, db_path=db_path)
       updated = get_hymn_by_id(hymn_id, db_path=db_path)
       return {"status": "success", "hymn": updated}
   ```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py::test_lyrics_api_endpoints -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/main.py tests/test_api.py
git commit -m "feat(api): add PUT /api/hymns/{id}/lyrics endpoint"
```

---

### Task 3: HTML & CSS Structure for Modal Tabs & Lyrics Views

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**

In `tests/test_e2e.py`, add `test_hymn_details_modal_tabs_and_lyrics_html`:

```python
def test_hymn_details_modal_tabs_and_lyrics_html():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Check tab buttons
    assert 'id="tab-btn-info"' in html
    assert 'id="tab-btn-lyrics"' in html
    assert 'switchHymnModalTab' in html

    # Check tab containers
    assert 'id="modal-tab-info-content"' in html
    assert 'id="modal-tab-lyrics-content"' in html

    # Check lyrics sub-views & elements
    assert 'id="lyrics-read-view"' in html
    assert 'id="lyrics-edit-view"' in html
    assert 'id="lyrics-empty-view"' in html
    assert 'id="lyrics-text"' in html
    assert 'id="lyrics-textarea"' in html
    assert 'btn-copy-lyrics' in html
    assert 'btn-edit-lyrics' in html
    assert 'btn-save-lyrics' in html
    assert 'btn-cancel-lyrics' in html
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e.py::test_hymn_details_modal_tabs_and_lyrics_html -v`
Expected: FAIL with `AssertionError: assert 'id="tab-btn-info"' in html`.

**Step 3: Write minimal implementation**

1. In `src/static/index.html`, inside `#hymn-details-modal .modal-body`:
   - Add tab bar:
     ```html
     <div class="modal-tabs">
       <button type="button" id="tab-btn-info" class="modal-tab-btn active" onclick="switchHymnModalTab('info')">Info & History</button>
       <button type="button" id="tab-btn-lyrics" class="modal-tab-btn" onclick="switchHymnModalTab('lyrics')">
         Lyrics <span id="modal-lyrics-badge" class="badge-dot hidden" title="Lyrics available"></span>
       </button>
     </div>
     ```
   - Wrap existing sections (`#modal-metadata-bar`, `#modal-history-heading`/container, `#modal-tune-heading`/container) in `<div id="modal-tab-info-content" class="modal-tab-pane">`.
   - Add lyrics tab content `<div id="modal-tab-lyrics-content" class="modal-tab-pane hidden">`:
     - Header actions with Copy, Edit, Save, Cancel buttons.
     - `#lyrics-read-view`: `<div id="lyrics-text" class="lyrics-text-display"></div>`.
     - `#lyrics-edit-view`: `<textarea id="lyrics-textarea" class="lyrics-textarea" rows="12" placeholder="Paste or type hymn lyrics here (separate stanzas with blank lines)..."></textarea>`.
     - `#lyrics-empty-view`: Empty state message with "Add Lyrics" button.
2. In `src/static/styles.css`:
   - Add `.modal-tabs`, `.modal-tab-btn`, `.modal-tab-btn.active`, `.badge-dot`.
   - Add `.lyrics-text-display` with `white-space: pre-wrap`, `line-height: 1.7`, `font-family: inherit`, and clean padding.
   - Add `.lyrics-textarea` with dark palette, clear borders, focus ring, and monospace/clean font.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e.py::test_hymn_details_modal_tabs_and_lyrics_html -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/static/index.html src/static/styles.css tests/test_e2e.py
git commit -m "feat(ui): add tabbed navigation and lyrics container to hymn details modal"
```

---

### Task 4: Frontend JavaScript Logic for Tab Switching, Lyrics Editing & Copying

**Files:**
- Modify: `src/static/app.js`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**

In `tests/test_e2e.py`, add `test_hymn_details_lyrics_js_logic`:

```python
def test_hymn_details_lyrics_js_logic():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "function switchHymnModalTab(" in js
    assert "function enterLyricsEditMode(" in js
    assert "function cancelLyricsEdit(" in js
    assert "async function saveHymnLyrics(" in js
    assert "async function copyHymnLyricsToClipboard(" in js
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e.py::test_hymn_details_lyrics_js_logic -v`
Expected: FAIL with `AssertionError: assert 'function switchHymnModalTab(' in js`.

**Step 3: Write minimal implementation**

In `src/static/app.js`:
1. Add state variable: `let activeModalHymn = null;`
2. Implement `switchHymnModalTab(tabName)` to toggle `.active` class on tab buttons and `.hidden` on `#modal-tab-info-content` vs `#modal-tab-lyrics-content`.
3. In `openHymnDetailsModal(hymnId)`:
   - Store `activeModalHymn = hymn;`.
   - Reset tab to `'info'`.
   - Check if `hymn.lyrics` exists; toggle `#modal-lyrics-badge`.
   - Populate `#lyrics-text` and `#lyrics-textarea`.
   - If `hymn.lyrics` is present, show `#lyrics-read-view`; otherwise show `#lyrics-empty-view`. Ensure `#lyrics-edit-view` is hidden.
4. Implement `enterLyricsEditMode()`:
   - Hide read & empty views, show `#lyrics-edit-view`.
   - Toggle button visibilities (show Save/Cancel, hide Edit/Copy).
   - Set `#lyrics-textarea.value = activeModalHymn?.lyrics || ''` and focus it.
5. Implement `cancelLyricsEdit()`:
   - Restore previous state: if `activeModalHymn?.lyrics`, show read view; else show empty view.
   - Hide edit view; restore Edit/Copy buttons.
6. Implement `saveHymnLyrics()`:
   - Read `#lyrics-textarea.value`.
   - Send `PUT /api/hymns/${activeModalHymn.id}/lyrics` with `{ lyrics: value }`.
   - On success: update `activeModalHymn.lyrics`, update `#lyrics-text.textContent`, show read/empty view accordingly, toggle badge dot, show success toast (`Lyrics saved successfully!`).
   - On error: keep textarea active, show error toast (`Failed to save lyrics`).
7. Implement `copyHymnLyricsToClipboard()`:
   - Copy `activeModalHymn.lyrics` via `navigator.clipboard.writeText(text)` (with `document.execCommand` fallback).
   - Show success toast (`Lyrics copied to clipboard!`).

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e.py::test_hymn_details_lyrics_js_logic -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/static/app.js tests/test_e2e.py
git commit -m "feat(ui): implement tab switching, lyrics editing, saving, and copying in app.js"
```

---

### Task 5: End-to-End Workflow Verification & Regression Testing

**Files:**
- Test: `tests/test_e2e.py`
- Test: `tests/test_api.py`

**Step 1: Write integration test**

In `tests/test_e2e.py`, add `test_lyrics_modal_full_integration`:
- Verify all HTML element IDs match between `index.html` and `app.js`.
- Verify CSS classes used in `app.js` are declared in `styles.css`.
- Test that modal reset clears dirty state when modal is closed via `closeHymnDetailsModal()`.

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e.py -v`
Expected: PASS

**Step 3: Run full regression test suite**

Run: `python -m pytest -v`
Expected: All 123+ tests PASS with zero regressions.

**Step 4: Final Task Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add integration tests for lyrics modal workflow"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-10-06-hymn-lyrics-display-and-editing-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration
**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
