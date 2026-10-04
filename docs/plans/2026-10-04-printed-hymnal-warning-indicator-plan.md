# Printed Hymnal Warning Indicator Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provide visual warning indicators in the catalog sidebar and Hymn Details modal for hymns whose numbers exceed the printed hymnal limit (#966) using a configurable runtime threshold.

**Architecture:** A configuration helper in `src/config.py` provides the maximum printed hymn number (default 966, overridable via `MAX_PRINTED_HYMN_NUMBER`). Query results in `src/database.py` dynamically annotate each hymn with `in_printed_hymnal: bool`. The frontend UI in `src/static/app.js`, `styles.css`, and `index.html` displays an amber badge in the catalog list and an explanatory alert banner in the Hymn Details modal.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, Vanilla HTML5/CSS3/JavaScript, Pytest.

---

### Task 1: Configuration Helper for Maximum Printed Hymn Number

**Files:**
- Modify: `src/config.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

Create `tests/test_config.py`:
```python
import os
from src.config import DEFAULT_MAX_PRINTED_HYMN, get_max_printed_hymn_number


def test_default_max_printed_hymn():
    if "MAX_PRINTED_HYMN_NUMBER" in os.environ:
        del os.environ["MAX_PRINTED_HYMN_NUMBER"]
    assert DEFAULT_MAX_PRINTED_HYMN == 966
    assert get_max_printed_hymn_number() == 966


def test_override_max_printed_hymn(monkeypatch):
    monkeypatch.setenv("MAX_PRINTED_HYMN_NUMBER", "950")
    assert get_max_printed_hymn_number() == 950


def test_invalid_max_printed_hymn_fallback(monkeypatch):
    monkeypatch.setenv("MAX_PRINTED_HYMN_NUMBER", "invalid_number")
    assert get_max_printed_hymn_number() == 966
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ImportError: cannot import name 'DEFAULT_MAX_PRINTED_HYMN' from 'src.config'`

**Step 3: Write minimal implementation**

In `src/config.py`:
```python
DEFAULT_MAX_PRINTED_HYMN = 966


def get_max_printed_hymn_number() -> int:
    """Return the maximum printed hymn number, honoring MAX_PRINTED_HYMN_NUMBER."""
    val = os.environ.get("MAX_PRINTED_HYMN_NUMBER", str(DEFAULT_MAX_PRINTED_HYMN))
    try:
        return int(val)
    except ValueError:
        return DEFAULT_MAX_PRINTED_HYMN
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_config.py src/config.py
git commit -m "feat(config): add max printed hymn number configuration helper"
```

---

### Task 2: Annotate Hymns with `in_printed_hymnal` in Database & API Layer

**Files:**
- Modify: `src/database.py`
- Test: `tests/test_database.py`
- Test: `tests/test_api.py`

**Step 1: Write the failing test**

In `tests/test_database.py`:
```python
def test_in_printed_hymnal_annotation(tmp_path):
    from src.database import init_db, save_hymns, search_hymns, get_hymn_by_id, get_all_hymns
    db_file = str(tmp_path / "test_hymnal_flag.db")
    init_db(db_file)
    
    sample_tracks = [
        {"disc_number": 1, "track_number": 1, "hymn_number": 500, "title": "In Pew Hymnal", "liturgical_season": "General"},
        {"disc_number": 1, "track_number": 2, "hymn_number": 966, "title": "Boundary Hymn", "liturgical_season": "General"},
        {"disc_number": 1, "track_number": 3, "hymn_number": 970, "title": "Digital Only Hymn", "liturgical_season": "General"},
        {"disc_number": 2, "track_number": 1, "hymn_number": None, "title": "Kyrie", "liturgical_season": "Divine Service 1"}
    ]
    save_hymns(sample_tracks, db_path=db_file)
    
    hymns = search_hymns(db_path=db_file)
    by_title = {h["title"]: h for h in hymns}
    
    assert by_title["In Pew Hymnal"]["in_printed_hymnal"] is True
    assert by_title["Boundary Hymn"]["in_printed_hymnal"] is True
    assert by_title["Digital Only Hymn"]["in_printed_hymnal"] is False
    assert by_title["Kyrie"]["in_printed_hymnal"] is True
    
    h_970 = by_title["Digital Only Hymn"]
    fetched = get_hymn_by_id(h_970["id"], db_path=db_file)
    assert fetched["in_printed_hymnal"] is False
```

In `tests/test_api.py`:
```python
def test_api_hymns_in_printed_hymnal_flag(client):
    res = client.get("/api/hymns")
    assert res.status_code == 200
    data = res.json()
    if data:
        for h in data:
            assert "in_printed_hymnal" in h
            if h.get("hymn_number") and int(h["hymn_number"]) > 966:
                assert h["in_printed_hymnal"] is False
            elif h.get("hymn_number") and int(h["hymn_number"]) <= 966:
                assert h["in_printed_hymnal"] is True
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_database.py::test_in_printed_hymnal_annotation tests/test_api.py::test_api_hymns_in_printed_hymnal_flag -v`
Expected: FAIL with `KeyError: 'in_printed_hymnal'`

**Step 3: Write minimal implementation**

In `src/database.py`:
Import `get_max_printed_hymn_number` from `src.config`:
```python
from src.config import get_max_printed_hymn_number


def is_in_printed_hymnal(hymn_number, max_num=None) -> bool:
    """Return True if hymn is in printed hymnal (or non-numbered liturgy), False if hymn_number > max_num."""
    if hymn_number is None:
        return True
    if max_num is None:
        max_num = get_max_printed_hymn_number()
    try:
        return int(hymn_number) <= max_num
    except (ValueError, TypeError):
        return True


def _annotate_hymn_dict(hymn_dict: dict, max_num=None) -> dict:
    if hymn_dict:
        hymn_dict["in_printed_hymnal"] = is_in_printed_hymnal(hymn_dict.get("hymn_number"), max_num=max_num)
    return hymn_dict
```
Apply `_annotate_hymn_dict` in `get_all_hymns()`, `search_hymns()`, and `get_hymn_by_id()`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_database.py::test_in_printed_hymnal_annotation tests/test_api.py::test_api_hymns_in_printed_hymnal_flag -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/database.py tests/test_database.py tests/test_api.py
git commit -m "feat(api): annotate hymn objects with in_printed_hymnal flag"
```

---

### Task 3: Catalog List Warning Badge & Styling

**Files:**
- Modify: `src/static/styles.css`
- Modify: `src/static/app.js`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**

In `tests/test_e2e.py`:
```python
def test_catalog_unprinted_hymnal_badge_rendering():
    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".badge-not-in-hymnal" in css

    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "badge-not-in-hymnal" in js
    assert "in_printed_hymnal === false" in js or "in_printed_hymnal" in js
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e.py::test_catalog_unprinted_hymnal_badge_rendering -v`
Expected: FAIL

**Step 3: Write minimal implementation**

In `src/static/styles.css`:
```css
.badge-not-in-hymnal {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.5);
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  white-space: nowrap;
  margin-left: 4px;
}
```

In `src/static/app.js` within `renderHymnList`:
```javascript
const unprintedBadge = (h.in_printed_hymnal === false)
  ? `<span class="badge badge-not-in-hymnal" title="Not in printed hymnal (LSB contains hymns 1–966)" style="cursor: help;">⚠️ Not in Hymnal</span>`
  : '';
```
Include `${unprintedBadge}` alongside the hymn badge in the title block.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e.py::test_catalog_unprinted_hymnal_badge_rendering -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/static/styles.css src/static/app.js tests/test_e2e.py
git commit -m "feat(ui): add warning badge for unprinted hymns in catalog sidebar"
```

---

### Task 4: Hymn Details Modal Warning Banner

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`
- Modify: `src/static/app.js`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**

In `tests/test_e2e.py`:
```python
def test_hymn_details_modal_unprinted_banner():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert "modal-warning-banner" in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".modal-warning-banner" in css

    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "modal-warning-banner" in js
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e.py::test_hymn_details_modal_unprinted_banner -v`
Expected: FAIL

**Step 3: Write minimal implementation**

In `src/static/index.html` inside `#hymn-details-modal .modal-body`:
```html
<div id="modal-warning-banner" class="modal-warning-banner hidden"></div>
```

In `src/static/styles.css`:
```css
.modal-warning-banner {
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.4);
  color: #fde68a;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 0.85rem;
  line-height: 1.4;
}
```

In `src/static/app.js` inside `openHymnDetailsModal`:
Reset/hide `modal-warning-banner` on open.
When hymn data is loaded:
```javascript
const bannerEl = document.getElementById('modal-warning-banner');
if (bannerEl) {
  if (hymn.in_printed_hymnal === false) {
    bannerEl.innerHTML = `⚠️ <strong>Accompaniment Track Only:</strong> This hymn (${escapeHtml(titleText)}) is not included in the printed hymnal (LSB contains hymns 1–966). A printed bulletin insert will be required for congregational singing.`;
    bannerEl.classList.remove('hidden');
  } else {
    bannerEl.classList.add('hidden');
    bannerEl.innerHTML = '';
  }
}
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e.py::test_hymn_details_modal_unprinted_banner -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/static/index.html src/static/styles.css src/static/app.js tests/test_e2e.py
git commit -m "feat(ui): display unprinted warning banner in hymn details modal"
```

---

### Task 5: Full Test Suite Verification

**Step 1: Run the full test suite**

Run: `python -m pytest -v`
Expected: All tests pass (115+ tests, 0 failures)

**Step 2: Commit**

```bash
git status
```
Ensure working tree is clean.
