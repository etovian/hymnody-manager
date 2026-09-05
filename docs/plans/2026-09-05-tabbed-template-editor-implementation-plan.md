# Tabbed Template Editor Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the right-hand panel of Hymnody Manager into two tabs (Service Planner and Template Editor), move template editing from a modal directly into Tab 2, and add a dedicated Template Selector Modal for choosing or creating setting templates.

**Architecture:** Frontend HTML/CSS/JS structural update with full drag-and-drop support from the left-hand Hymnal Catalog (Hymns/Liturgy) into the Tab 2 Template Editor, integrated with existing SQLite template REST APIs (`GET/POST/PUT/DELETE /api/templates`).

**Tech Stack:** Vanilla HTML5, CSS3, JavaScript (ES6+), FastAPI, SQLite, Pytest, Playwright (E2E testing).

---

### Task 1: Add Right-Panel Tab Navigation & Layout in HTML/CSS

**Files:**
- Modify: `src/static/index.html:56-115`, `src/static/index.html:191-246`
- Modify: `src/static/styles.css`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing E2E test for right-panel tabs**

Add a test in `tests/test_e2e.py` checking for `#tab-service-planner` and `#tab-template-editor` elements.

```python
def test_right_panel_tabs_exist(page: Page, server_url: str):
    page.goto(server_url)
    assert page.is_visible("#tab-service-planner")
    assert page.is_visible("#tab-template-editor")
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_e2e.py::test_right_panel_tabs_exist -v`  
Expected: FAIL (element `#tab-service-planner` not found)

**Step 3: Modify HTML & CSS to add right-panel tabs**

1. In `src/static/index.html`, add tab buttons inside the right-column card:
   - `#tab-service-planner` (active by default)
   - `#tab-template-editor`
2. Wrap existing planner content in `#panel-service-planner`.
3. Add `#panel-template-editor` with template active banner, `#btn-open-template-modal`, slot editor, and save/delete buttons.
4. Replace `#template-editor-modal` with `#template-selector-modal` containing `#template-cards-container` and `➕ Create New Blank Template`.
5. Add CSS in `src/static/styles.css` for tab buttons, template cards grid, and active banner.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_e2e.py::test_right_panel_tabs_exist -v`  
Expected: PASS

**Step 5: Commit**

`git add src/static/index.html src/static/styles.css tests/test_e2e.py`  
`git commit -m "feat: add right panel tabbed layout HTML and CSS"`

---

### Task 2: Implement Tab Switching & Template Selector Modal Logic in `app.js`

**Files:**
- Modify: `src/static/app.js:816-1090`
- Test: `tests/test_e2e.py`

**Step 1: Write failing E2E test for tab switching & opening template selector modal**

```python
def test_open_template_selector_modal(page: Page, server_url: str):
    page.goto(server_url)
    page.click("#tab-template-editor")
    assert page.is_visible("#panel-template-editor")
    page.click("#btn-open-template-modal")
    assert page.is_visible("#template-selector-modal")
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_e2e.py::test_open_template_selector_modal -v`  
Expected: FAIL (`#tab-template-editor` click or modal display not found)

**Step 3: Implement JavaScript handlers in `app.js`**

1. `switchPlannerTab(tab)`: Toggles active classes for `#tab-service-planner` and `#tab-template-editor`, shows/hides `#panel-service-planner` and `#panel-template-editor`.
2. `openTemplateSelectorModal()` & `closeTemplateSelectorModal()`: Shows/hides `#template-selector-modal`.
3. `renderTemplateCardsModal(templates)`: Renders template cards in the modal with `Select for Editing` and `📋 Duplicate` buttons.
4. `selectTemplateFromModal(templateId)`: Sets `selectedTemplateForEdit`, populates Tab 2 form fields, and closes modal.
5. `duplicateTemplateFromModal(templateId)`: Creates copy of selected template, saves as new custom template, and opens in Tab 2.
6. `createNewTemplateFromModal()`: Initializes blank custom template in Tab 2 and closes modal.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_e2e.py::test_open_template_selector_modal -v`  
Expected: PASS

**Step 5: Commit**

`git add src/static/app.js tests/test_e2e.py`  
`git commit -m "feat: implement tab switching and template selector modal logic"`

---

### Task 3: Support Drag-and-Drop Audio Binding & Template Saving in Tab 2

**Files:**
- Modify: `src/static/app.js:935-1090`
- Test: `tests/test_e2e.py`

**Step 1: Write failing E2E test for editing and saving custom template in Tab 2**

```python
def test_create_and_save_custom_template_in_tab2(page: Page, server_url: str):
    page.goto(server_url)
    page.click("#tab-template-editor")
    page.click("#btn-open-template-modal")
    page.click("#btn-new-template-modal")
    page.fill("#edit-template-name", "Test Service Setting")
    page.click("#btn-save-template")
    page.click("#tab-service-planner")
    options = page.eval_on_selector_all("#preset-select option", "opts => opts.map(o => o.value)")
    assert "Test Service Setting" in options
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_e2e.py::test_create_and_save_custom_template_in_tab2 -v`  
Expected: FAIL

**Step 3: Implement drag-drop and save/delete logic in Tab 2**

1. Update `onTemplateListDrop` & `onTemplateSlotDrop` in `app.js` to accept drops from catalog items (both Hymn and Liturgy tabs).
2. Connect `saveTemplateFromUI()` to refresh both `#preset-select` in Tab 1 and the modal cards list.
3. Connect `deleteTemplateUI()` to delete custom templates and reset Tab 2 to a default template.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_e2e.py::test_create_and_save_custom_template_in_tab2 -v`  
Expected: PASS

**Step 5: Commit**

`git add src/static/app.js tests/test_e2e.py`  
`git commit -m "feat: enable drag-and-drop audio binding and template saving in Tab 2"`

---

### Task 4: Full Suite Verification & E2E Validation

**Files:**
- Test: `tests/`

**Step 1: Run full test suite**

Run: `pytest -v`  
Expected: 100% tests PASS (all backend unit tests and frontend E2E tests).

**Step 2: Commit final verification**

`git commit --allow-empty -m "test: verify right panel tabbed template editor redesign"`
