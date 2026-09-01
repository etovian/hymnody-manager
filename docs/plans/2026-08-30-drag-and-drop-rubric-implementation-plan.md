# Drag-and-Drop & Rubric Conformance Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement dual HTML5 drag-and-drop (Catalog-to-Slot dropping & In-List reordering), item deletion, and real-time liturgical rubric conformance validation with status badges and template restoration.

**Architecture:** Extend `src/static/app.js` with HTML5 Drag-and-Drop event handlers (`dragstart`, `dragover`, `drop`), rubric validation algorithms, status badge DOM rendering, and API synchronization with `/api/services/{id}/items`. Add unit/e2e tests in `tests/test_rubric.py`.

**Tech Stack:** HTML5 Drag & Drop API, Vanilla JS, CSS3, FastAPI, pytest.

---

### Task 1: Rubric Validator & Preset Conformance Engine Backend/Frontend

**Files:**
- Create: `tests/test_rubric.py`
- Modify: `src/services.py`
- Modify: `src/static/app.js`

**Step 1: Write failing rubric validation test**

```python
# tests/test_rubric.py
from src.database import init_db, save_hymns
from src.services import create_service_from_preset, validate_service_rubric

def test_rubric_validation_standard_and_modified(tmp_path):
    db_path = str(tmp_path / "rubric_test.db")
    init_db(db_path)
    
    # Create standard DS2 service
    srv_id = create_service_from_preset("Standard Service", "2026-08-30", "DS2", db_path=db_path)
    
    status = validate_service_rubric(srv_id, db_path=db_path)
    assert status['is_conformant'] is True
    assert len(status['issues']) == 0
```

**Step 2: Implement rubric validation helper in `src/services.py`**

```python
# In src/services.py
def validate_service_rubric(service_id, db_path="hymnody.db"):
    srv = get_service_details(service_id, db_path=db_path)
    if not srv:
        return {'is_conformant': False, 'issues': ['Service not found']}
        
    setting = srv.get('setting_preset', 'DS2')
    expected_slots = PRESETS.get(setting, [])
    actual_items = srv.get('items', [])
    
    issues = []
    # Check for missing required canticles
    for slot_name, match_term, item_title in expected_slots:
        if match_term != "HYMN_SLOT":
            found = any(match_term.lower() in item.get('item_title', '').lower() or match_term.lower() in item.get('slot_name', '').lower() for item in actual_items)
            if not found:
                issues.append(f"Missing required canticle: {item_title}")
                
    return {
        'is_conformant': len(issues) == 0,
        'issues': issues,
        'setting': setting
    }
```

**Step 3: Add API route `/api/services/{id}/rubric` in `src/main.py`**

```python
# In src/main.py
from src.services import validate_service_rubric

@app.get("/api/services/{service_id}/rubric")
def api_validate_rubric(service_id: int):
    db_path = get_db_path()
    return validate_service_rubric(service_id, db_path=db_path)
```

---

### Task 2: HTML5 Drag-and-Drop & Rubric Status UI

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`
- Modify: `src/static/app.js`

**Step 1: Update `src/static/index.html` with Rubric Status Badge & Popover**

Add status badge in service plan header:
```html
<div class="rubric-status-container">
  <span id="rubric-badge" class="rubric-badge conformant" onclick="toggleRubricPopover()">✓ Standard DS2 Rubric</span>
  <div id="rubric-popover" class="rubric-popover hidden">
    <h4>Rubric Conformance Details</h4>
    <ul id="rubric-issues-list"></ul>
    <button class="btn btn-primary btn-sm mt-2" onclick="restoreOfficialPreset()">🔄 Restore Official Template</button>
  </div>
</div>
```

**Step 2: Add Drag & Drop handlers in `src/static/app.js`**

- Catalog items `draggable="true"`, `ondragstart="onHymnDragStart(event, hymnId)"`.
- Service slots `ondragover="onDragOver(event)"`, `ondragleave="onDragLeave(event)"`, `ondrop="onHymnDrop(event, slotIndex)"`.
- Item reorder drag handles `draggable="true"`, `ondragstart="onItemDragStart(event, itemIndex)"`, `ondrop="onItemDrop(event, targetIndex)"`.
- Item removal button `onclick="removeServiceItem(index)"`.
- Live `fetchRubricStatus()` call on every item drop, reorder, or deletion.

---

### Task 3: Verification & Test Suite

**Files:**
- Run: `pytest -v`
