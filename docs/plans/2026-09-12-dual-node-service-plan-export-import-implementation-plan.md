# Dual Node Service Plan Export/Import & UI Real Estate Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable dual-node operation by exporting and importing portable `.hymnody` JSON service plan files, and optimize Worship Planner header UI real estate with a unified Export dropdown menu and inline title/rubric placement.

**Architecture:** 
- `src/exporter.py` handles serialization of service records into the `.hymnody` JSON schema.
- `src/services.py` implements the track matching algorithm `(disc, track)` -> `(hymn_number, title)` -> local audio file verification.
- `src/main.py` exposes `GET /api/services/{id}/export-plan` and `POST /api/services/import-plan`.
- `src/static/app.js`, `index.html`, and `styles.css` update the header layout, add an Export dropdown, and implement an Import preview modal.

**Tech Stack:** Python 3.10+, FastAPI, SQLite3, HTML5/CSS3, Vanilla JS.

---

### Task 1: Service Plan JSON Serialization & Import Matching Logic

**Files:**
- Modify: `src/exporter.py`
- Modify: `src/services.py`
- Test: `tests/test_exporter.py`
- Test: `tests/test_services.py`

**Step 1: Write failing test for `export_service_plan_json` and `import_service_plan_json`**

In `tests/test_exporter.py`:
```python
def test_export_service_plan_json():
    # Test exporting a service plan to .hymnody JSON structure
    from src.exporter import export_service_plan_json
    # Expected output contains 'version', 'service', 'items' with disc/track and hymn_number
```

In `tests/test_services.py`:
```python
def test_import_service_plan_json():
    # Test importing .hymnody JSON and resolving hymn IDs against target DB
    from src.services import import_service_plan_json
```

**Step 2: Run tests to verify failure**
Run: `pytest tests/test_exporter.py tests/test_services.py -v`
Expected: FAIL with `ImportError: cannot import name 'export_service_plan_json'`

**Step 3: Implement serialization in `src/exporter.py` and matching in `src/services.py`**
- Implement `export_service_plan_json(service_id, db_path)` in `src/exporter.py`.
- Implement `import_service_plan_json(data, db_path)` in `src/services.py` with multi-stage matching `(disc, track)` -> `(hymn_number, title)` -> disk existence check.

**Step 4: Run tests to verify pass**
Run: `pytest tests/test_exporter.py tests/test_services.py -v`
Expected: PASS

**Step 5: Commit**
Command: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/exporter.py', 'src/services.py', 'tests/test_exporter.py', 'tests/test_services.py']); subprocess.run(['git', 'commit', '-m', 'feat: add service plan json serialization and matching logic'])"`

---

### Task 2: REST API Endpoints for Service Plan Export and Import

**Files:**
- Modify: `src/main.py`
- Test: `tests/test_api.py`

**Step 1: Write failing API tests**

In `tests/test_api.py`:
```python
def test_export_service_plan_endpoint(client):
    response = client.get("/api/services/1/export-plan")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

def test_import_service_plan_endpoint(client):
    payload = {...}
    response = client.post("/api/services/import-plan", json=payload)
    assert response.status_code == 200
    assert "imported_service_id" in response.json()
```

**Step 2: Run test to verify failure**
Run: `pytest tests/test_api.py -k "test_export_service_plan_endpoint or test_import_service_plan_endpoint" -v`
Expected: FAIL (404 Not Found)

**Step 3: Add routes in `src/main.py`**
- `GET /api/services/{service_id}/export-plan`
- `POST /api/services/import-plan`

**Step 4: Run test to verify pass**
Run: `pytest tests/test_api.py -v`
Expected: PASS

**Step 5: Commit**
Command: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/main.py', 'tests/test_api.py']); subprocess.run(['git', 'commit', '-m', 'feat: add service plan export and import API endpoints'])"`

---

### Task 3: Worship Planner Header UI & Export Dropdown Optimization

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`
- Test: `tests/test_e2e.py` (or static verification)

**Step 1: Write failing test or UI element assertion**
Verify presence of unified Export dropdown `#export-dropdown-btn` and `#import-plan-btn` in `tests/test_e2e.py` or DOM check.

**Step 2: Implement header layout changes**
- Move `#rubric-validation-badge` inline next to `#service-title` inside `#service-title-container`.
- Fix premature title wrapping in `styles.css`.
- Replace single Export button with `#export-dropdown-container` containing `#export-dropdown-btn` and dropdown items (`#export-zip-option`, `#export-json-option`).
- Add `#import-plan-btn` and hidden file input `#plan-file-input`.

**Step 3: Verify visually and via tests**
Run: `pytest tests/test_e2e.py -v`

**Step 4: Commit**
Command: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/styles.css']); subprocess.run(['git', 'commit', '-m', 'ui: optimize header layout and add unified export dropdown'])"`

---

### Task 4: Frontend Import/Export Event Handlers & Preview Modal

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/app.js`

**Step 1: Implement modal HTML in `src/static/index.html`**
Add `#import-plan-modal` structure with title, summary list, track matching stats, and `Confirm` / `Cancel` buttons.

**Step 2: Implement JavaScript logic in `src/static/app.js`**
- Handle dropdown toggle state.
- Wire `.hymnody` export download trigger (`/api/services/${id}/export-plan`).
- Handle file selection & drag-and-drop `.hymnody` file parsing.
- Show preview modal with match statistics before calling `/api/services/import-plan`.
- Refresh service list and navigate to imported service upon confirmation.

**Step 3: Run pytest suite to ensure zero regressions**
Run: `pytest -v`
Expected: ALL PASS

**Step 4: Commit**
Command: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat: implement frontend plan export/import and confirmation modal'])"`
