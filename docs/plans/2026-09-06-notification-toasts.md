# Notification Toasts Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a lightweight, non-intrusive notification toast engine in Hymnody Manager to display info, success, warning, and error messages to users across all planner, template, export, and network actions.

**Architecture:** Add a fixed top-right overlay container `#toast-container` in `src/static/index.html` styled with dark theme card aesthetics, entrance/exit CSS slide animations in `src/static/styles.css`, and a `showToast()` JavaScript API in `src/static/app.js` with auto-dismiss timers, max stack capping (5 toasts), sticky error handling, and complete event triggers.

**Tech Stack:** Vanilla JavaScript, HTML5, CSS3, FastAPI (Python), Pytest (Test Suite).

---

### Task 1: Add Toast Container DOM & CSS Styles

**Files:**
- Modify: `src/static/index.html:10-15`
- Modify: `src/static/styles.css:700-800`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**
In `tests/test_e2e.py`, add a test `test_index_contains_toast_container()` verifying that GET `/` returns HTML containing `<div id="toast-container"`.

```python
def test_index_contains_toast_container():
    res = client.get("/")
    assert res.status_code == 200
    assert '<div id="toast-container"' in res.text
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_e2e.py::test_index_contains_toast_container -v`
Expected: FAIL (assertion error `<div id="toast-container"` not in response).

**Step 3: Write minimal implementation**
1. In `src/static/index.html`, add `<div id="toast-container" class="toast-container"></div>` right after `<body>`.
2. In `src/static/styles.css`, add container and card styles:
   - `.toast-container`: `position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; max-width: 380px; pointer-events: none;`
   - `.toast`: `pointer-events: auto; display: flex; align-items: flex-start; gap: 10px; background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-left: 4px solid #3b82f6; padding: 12px 14px; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4); animation: slideInRight 0.25s ease-out forwards;`
   - Border colors: `.toast-success` (`#10b981`), `.toast-info` (`#3b82f6`), `.toast-warning` (`#f59e0b`), `.toast-error` (`#ef4444`).
   - Keyframes: `@keyframes slideInRight` and `@keyframes fadeOutRight`.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_e2e.py::test_index_contains_toast_container -v`
Expected: PASS.

**Step 5: Commit**
Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/styles.css', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'feat: add toast container DOM structure and CSS styles'])"`

---

### Task 2: Implement Toast Notification Engine (`showToast`) in `app.js`

**Files:**
- Modify: `src/static/app.js`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**
In `tests/test_e2e.py`, add `test_app_js_includes_show_toast()` checking that `app.js` contains the definition for `showToast`.

```python
def test_app_js_includes_show_toast():
    res = client.get("/static/app.js?v=2")
    assert res.status_code == 200
    assert "function showToast" in res.text
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_e2e.py::test_app_js_includes_show_toast -v`
Expected: FAIL.

**Step 3: Write minimal implementation**
Implement `showToast(message, type = 'info', title = null, duration = null)` in `src/static/app.js`:
- Define icons for `success` (🟢 `✓`), `info` (🔵 `ℹ`), `warning` (🟡 `⚠`), `error` (🔴 `✕`).
- Default durations: `success`/`info` = 4000ms, `warning` = 8000ms, `error` = 0 (sticky/manual close).
- Enforce max 5 toast items: if `toastContainer.children.length >= 5`, remove oldest.
- Create elements, attach close button click listener to invoke removal with exit animation.
- Set `setTimeout` to dismiss automatically if duration > 0.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_e2e.py::test_app_js_includes_show_toast -v`
Expected: PASS.

**Step 5: Commit**
Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'feat: implement showToast notification engine in app.js'])"`

---

### Task 3: Wire Toast Notifications into Service Planner Workflow

**Files:**
- Modify: `src/static/app.js`

**Step 1: Inspect functions to update**
Functions in `app.js`:
- `saveActiveServiceUI()`: Add `showToast("Service plan saved successfully", "success", "Plan Saved")` on success, `showToast(err.message || "Failed to save service plan", "error", "Save Failed")` on catch.
- `deleteService()`: Add `showToast("Service plan deleted", "warning", "Service Deleted")` on success.
- `createNewService()`: Add `showToast("Created new service plan", "info", "New Service")`.
- `changeSettingPreset()`: Add `showToast(`Switched setting preset to ${presetKey}`, "info")`.

**Step 2: Implement changes**
Add `showToast()` calls into `saveActiveServiceUI`, `deleteService`, `createNewService`, and `changeSettingPreset`.

**Step 3: Test full pytest test suite**
Run: `pytest -v`
Expected: PASS.

**Step 4: Commit**
Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat: add toast notifications to service planner actions'])"`

---

### Task 4: Wire Toast Notifications into Template Editor Workflow

**Files:**
- Modify: `src/static/app.js`

**Step 1: Inspect functions to update**
Functions in `app.js`:
- `saveActiveTemplateUI()`: Add `showToast(`Template '${title}' saved successfully`, "success", "Template Saved")` on success, and error toast on catch.
- `deleteTemplateUI()`: Add `showToast("Template removed", "warning", "Template Deleted")` on success.
- `createNewTemplateFromModal()`: Add `showToast("New template created", "success")`.

**Step 2: Implement changes**
Add `showToast()` calls into template editor handlers in `src/static/app.js`.

**Step 3: Run test suite**
Run: `pytest -v`
Expected: PASS.

**Step 4: Commit**
Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat: add toast notifications to template editor actions'])"`

---

### Task 5: Wire Toast Notifications into Mobile Exporter & API Error Handlers

**Files:**
- Modify: `src/static/app.js`

**Step 1: Inspect functions to update**
Functions in `app.js`:
- `exportMobileZip()`: Add `showToast("Generating mobile ZIP package...", "info")` at start, `showToast("Mobile package downloaded successfully", "success")` on success, and warning toast if missing audio files exist.
- Catch blocks in `fetchHymns()`, `fetchOrCreateService()`, `loadTemplatesUI()`, etc.: Add `showToast("Network request failed", "error", "API Error")`.

**Step 2: Implement changes**
Add `showToast()` calls into `exportMobileZip()` and remaining API `catch` blocks in `src/static/app.js`.

**Step 3: Run test suite**
Run: `pytest -v`
Expected: PASS.

**Step 4: Commit**
Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat: add toast notifications to mobile exporter and API errors'])"`

---

### Task 6: Comprehensive E2E Verification & Test Suite Execution

**Files:**
- Modify: `tests/test_e2e.py`

**Step 1: Add E2E Toast integration assertions**
Verify in `tests/test_e2e.py` that index served by FastAPI includes toast styles link and toast container.

**Step 2: Run full test suite**
Run: `pytest -v`
Expected: 100% passing tests (all tests green).

**Step 3: Commit**
Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'test: verify full test suite with notification toasts'])"`
