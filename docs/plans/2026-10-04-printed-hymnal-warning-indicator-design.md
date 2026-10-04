# Printed Hymnal Warning Indicator Design Specification

## Overview

The *Lutheran Service Book* (LSB) printed hymnal contains hymns numbered up to **#966**. The accompaniment audio collection (*The Concordia Organist*) includes additional supplemental audio tracks with hymn numbers up to **#986**. 

When planning services, pastors and worship coordinators need immediate visual feedback if a selected or browsed hymn does not appear in the printed pew hymnal. Without this indicator, a congregation may lack hymn text and notation unless a bulletin insert is prepared.

This feature adds a warning indicator to hymns in the catalog sidebar and Hymn Details modal when the hymn number exceeds the printed hymnal limit.

---

## Key Requirements & Non-Requirements

### Requirements
1. **Configurable Threshold**:
   - Default maximum printed hymn number is `966`.
   - Configurable via `MAX_PRINTED_HYMN_NUMBER` environment variable in `src/config.py`.
2. **Runtime Calculation (No DB Schema Migration)**:
   - Evaluated dynamically at request runtime when returning hymn objects.
   - Hymn numbers $> 966$ receive `in_printed_hymnal: false`.
   - Hymn numbers $\le 966$ and liturgical tracks receive `in_printed_hymnal: true`.
3. **Visual Indicator in Hymn Catalog**:
   - Catalog sidebar list items display an amber warning badge / icon (`⚠️`) alongside the hymn badge with tooltip text:
     `Not in printed hymnal (LSB contains hymns 1–966)`.
4. **Hymn Details Modal Callout**:
   - When viewing hymn details in the modal, a clear amber notice banner alerts the user:
     `⚠️ Accompaniment Track Only: Not included in printed hymnal (LSB contains hymns 1–966). A printed bulletin insert will be required for congregational singing.`

### Non-Requirements
- No SQLite schema changes or database migrations.
- No blocking or restriction on selecting, planning, or playing tracks $> 966$.

---

## Technical Architecture & Changes

### 1. Configuration (`src/config.py`)
Add helper function and default:
```python
DEFAULT_MAX_PRINTED_HYMN = 966

def get_max_printed_hymn_number() -> int:
    """Return the maximum printed hymn number, defaulting to 966."""
    val = os.environ.get("MAX_PRINTED_HYMN_NUMBER", str(DEFAULT_MAX_PRINTED_HYMN))
    try:
        return int(val)
    except ValueError:
        return DEFAULT_MAX_PRINTED_HYMN
```

### 2. Backend API Layer (`src/main.py` & `src/database.py`)
Add helper to annotate hymn objects with `in_printed_hymnal`:
```python
def annotate_hymn_printed_status(hymn: dict, max_num: int) -> dict:
    raw_num = hymn.get("hymn_number")
    if raw_num is not None:
        try:
            hymn["in_printed_hymnal"] = int(raw_num) <= max_num
        except (ValueError, TypeError):
            hymn["in_printed_hymnal"] = True
    else:
        hymn["in_printed_hymnal"] = True
    return hymn
```
Annotate hymns in `/api/hymns` (catalog search/list) and `/api/hymns/{hymn_id}` (detail endpoint).

### 3. Frontend UI (`src/static/app.js` & `src/static/styles.css`)
- In `renderHymnList(hymns)`:
  - If `h.in_printed_hymnal === false`, append a warning indicator badge:
    ```html
    <span class="badge warning-badge" title="Not in printed hymnal (LSB contains hymns 1–966)" style="cursor: help;">⚠️ Not in Hymnal</span>
    ```
- In `openHymnDetailsModal(hymnId)`:
  - If `hymn.in_printed_hymnal === false`, display an alert banner:
    ```html
    <div class="hymn-modal-warning-banner">
      ⚠️ <strong>Accompaniment Track Only:</strong> This hymn (#${escapeHtml(hymn.hymn_number)}) is not included in the printed hymnal (LSB contains hymns 1–966). A printed bulletin insert will be required for congregational singing.
    </div>
    ```
- CSS styles for `.warning-badge` and `.hymn-modal-warning-banner`.

---

## Verification & Testing Strategy

1. **Unit & API Tests (`tests/test_api.py`)**:
   - Verify `/api/hymns` returns `in_printed_hymnal: True` for hymns $\le 966$.
   - Verify `/api/hymns` returns `in_printed_hymnal: False` for hymns $> 966$ (e.g. #970, #986).
   - Verify liturgical tracks and null hymn numbers default to `True`.
   - Verify `MAX_PRINTED_HYMN_NUMBER` environment variable override functions as expected.
2. **Frontend UI Tests / Manual Verification**:
   - Confirm warning badge renders in the catalog list for hymns $> 966$.
   - Confirm details modal displays the warning banner.
