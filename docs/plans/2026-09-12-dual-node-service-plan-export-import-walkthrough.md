# Dual Node Service Plan Export/Import & UI Optimization Walkthrough

## Summary of Changes

We implemented a complete **Dual Node** offline sync solution for Hymnody Manager along with Worship Planner UI header optimizations.

### 1. Backend Serialization & Audio Track Matching Algorithm (`src/exporter.py` & `src/services.py`)
- **JSON Serialization**: `export_service_plan_json(service_id)` serializes services into portable `.hymnody` JSON files containing title, date, liturgical day, preset name, and items with `disc_number`, `track_number`, `hymn_number`, `title`, and `tune`.
- **Import Resolution**: `import_service_plan_json(plan_data)` parses incoming plan files and matches audio tracks on the target node using:
  1. `(disc_number, track_number)`
  2. `(hymn_number, title)`
  3. `title`
  Checks local disk file existence (`file_path`). If audio is missing, marks the slot with missing audio alerts while preserving plan items.

### 2. REST API Endpoints (`src/main.py`)
- **`GET /api/services/{service_id}/export-plan`**: Downloads formatted `.hymnody` JSON files with `Content-Disposition: attachment; filename="[Date]_[Preset]_[Title].hymnody"`.
- **`POST /api/services/import-plan`**: Accepts plan payload, creates service in target node database, and returns audio track match stats.

### 3. UI Header Space Optimization & Unified Export Dropdown (`src/static/index.html` & `src/static/styles.css`)
- **Inline Title & Rubric Badge**: Moved the Rubric Conformance Badge (`✓ Standard Rubric`) inline onto the title line with flex wrapping adjustments to fix premature title wrapping.
- **Unified Export Dropdown (`📦 Export ▾`)**: Consolidated export options into a clean dropdown menu:
  - `📦 Mobile Audio Package (.zip)`
  - `📄 Service Plan File (.hymnody)`
- **Import Button & Drag-and-Drop**: Added `📥 Import` button and full-window drag-and-drop listener for `.hymnody` and `.json` files.

### 4. Import Confirmation Preview Modal (`src/static/index.html` & `src/static/app.js`)
- Displays service plan details (title, date, preset, total items) and live audio matching stats (`X Matched`, `Y Missing Alert`) before committing the plan to `hymnody.db`.

---

## Verification Results

### Automated Tests
Ran full test suite (`pytest -v`):
```
collected 82 items
82 passed in 17.03s
```
- `tests/test_exporter.py::test_export_service_plan_json`: **PASSED**
- `tests/test_services.py::test_import_service_plan_json`: **PASSED**
- `tests/test_api.py::test_export_service_plan_api`: **PASSED**
- `tests/test_api.py::test_import_service_plan_api`: **PASSED**
