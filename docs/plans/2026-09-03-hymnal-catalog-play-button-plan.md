# Hymnal Catalog & Template Editor "Play" Button Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the `+ Add` button with a `▶ Play` button in both the main Hymnal Catalog list and the Template Editor modal catalog search list.

**Architecture:** Update `src/static/app.js` to add `playCatalogHymn(hymnId)` for instant audio streaming in the audio player bar, replace `+ Add` button HTML rendering in `renderHymnList` and `searchModalCatalog`, retain drag-and-drop capability, and update the test suite to verify the UI changes.

**Tech Stack:** JavaScript (ES6), HTML5, FastAPI, pytest

---

### Task 1: Frontend Catalog Audio Playback & UI Update

**Files:**
- Modify: `src/static/app.js`

**Step 1: Write `playCatalogHymn(hymnId)` helper and update button markup**

In `src/static/app.js`:
- Add `playCatalogHymn(hymnId)` function.
- Update `renderHymnList` button HTML from `+ Add` to `▶ Play`.
- Update `searchModalCatalog` button HTML from `+ Add` to `▶ Play`.

**Step 2: Commit changes**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat: replace + Add button with Play button in hymnal catalog and template editor'])"
```

---

### Task 2: Automated Tests & Verification

**Files:**
- Modify: `tests/test_e2e.py`

**Step 1: Update/Add E2E tests for catalog Play buttons**

Add assertions checking that catalog HTML response contains `playCatalogHymn` and `▶ Play`.

**Step 2: Run test suite**

Run: `pytest -v`

**Step 3: Commit test updates**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'test: verify catalog Play buttons in e2e test suite'])"
```
