# Elevate Liturgical Day & Remove Service Title Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the static "Sunday Worship Service" title from desktop and mobile UIs and elevate the liturgical day (with date/setting fallback) into the primary heading position across all views, modals, and dropdowns.

**Architecture:** Introduce a unified heading formatting helper in `src/static/app.js` that evaluates `liturgical_day` and falls back to `"${service_date} • ${setting_preset}"`. Update desktop header rendering, mobile sanctuary header rendering, services explorer cards, and dropdown options to use this heading, while streamlining subtitles to display date, setting, and mode without redundant liturgical day text. Retain backend SQLite schema compatibility by defaulting backend `title` to liturgical day or a generic service descriptor.

**Tech Stack:** Vanilla JavaScript (ES6+), HTML5, CSS3, Python 3.11, FastAPI, pytest.

---

### Task 1: Add Unit Tests for Liturgical Day Heading & UI Elevation

**Files:**
- Create: `tests/test_elevate_liturgical_day.py`

**Step 1: Write the failing test**

Create `tests/test_elevate_liturgical_day.py` asserting:
1. `src/static/index.html` does not contain the static text `"Sunday Worship Service"` or `"Service Plan: Loading..."`.
2. `src/static/app.js` defines and uses `getServiceHeading` logic that prioritizes `liturgical_day` and falls back to date and preset.
3. Desktop header (`#service-title-display`) renders `getServiceHeading` instead of `"Service Plan: " + title`.
4. Mobile header (`#mobile-service-title`) renders `getServiceHeading` instead of `service.title`.
5. Desktop and mobile subtitles display `Date: ... | Setting: ...` without duplicate liturgical day text.
6. Services Explorer cards and service dropdowns display liturgical day instead of hardcoded title.

```python
import pytest

def test_index_html_no_static_sunday_worship_service():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert "Sunday Worship Service" not in html
    assert "Service Plan: Loading..." not in html
    assert 'id="service-title-display"' in html
    assert 'id="mobile-service-title"' in html

def test_app_js_service_heading_helper():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "function getServiceHeading(" in js
    assert "service.liturgical_day" in js

def test_app_js_desktop_header_elevation():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "getServiceHeading(service)" in js
    assert "Service Plan: ${service.title" not in js

def test_app_js_mobile_header_elevation():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "getServiceHeading(mobileService)" in js
    assert "mobileService.title || 'Sunday Service'" not in js

def test_app_js_explorer_and_dropdown_elevation():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "getServiceHeading(s)" in js
    assert "Sunday Worship Service" not in js
```

**Step 2: Run test to verify it fails**

Run: `python -c "import subprocess; res = subprocess.run(['pytest', 'tests/test_elevate_liturgical_day.py', '-v'], capture_output=True, text=True); print(res.stdout); print(res.stderr)"`  
Expected: FAIL (assertions fail because `index.html` and `app.js` still contain the old strings and lack `getServiceHeading`).

**Step 3: Commit the failing test**

```bash
git add tests/test_elevate_liturgical_day.py
git commit -m "test: add test suite for elevating liturgical day and removing service title"
```

---

### Task 2: Update `src/static/index.html` Header Placeholders

**Files:**
- Modify: `src/static/index.html:69-85`, `src/static/index.html:195-200`

**Step 1: Implement the changes**
- In Desktop Planner (`#desktop-view`):
  - Replace `<h2 id="service-title-display" ...>Service Plan: Loading...</h2>` with `<h2 id="service-title-display" style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin: 0; display: inline;">Loading Service...</h2>`.
  - Replace `<p id="service-subtitle-display" ...>Date: -- | Setting: --</p>` with `<p id="service-subtitle-display" class="subtitle mb-2" style="font-size: 0.8rem; color: #94a3b8;">Date: -- | Setting: --</p>`.
- In Sanctuary Mobile Mode (`#mobile-view`):
  - Replace `<h2 id="mobile-service-title" ...>Sunday Worship Service</h2>` with `<h2 id="mobile-service-title" style="font-size: 1.5rem; font-weight: 800; color: white;">Loading Service...</h2>`.
  - Replace `<p id="mobile-service-subtitle" ...>Divine Service Setting Two</p>` with `<p id="mobile-service-subtitle" class="subtitle">Date: -- | Setting: --</p>`.

**Step 2: Verify HTML structure**

Run: `python -c "import subprocess; res = subprocess.run(['pytest', 'tests/test_html_validator.py', '-v'], capture_output=True, text=True); print(res.stdout); print(res.stderr)"`  
Expected: PASS.

**Step 3: Commit**

```bash
git add src/static/index.html
git commit -m "refactor(ui): update html header placeholders removing Sunday Worship Service"
```

---

### Task 3: Implement `getServiceHeading` and Elevate Heading in `src/static/app.js`

**Files:**
- Modify: `src/static/app.js`

**Step 1: Implement `getServiceHeading` and update header rendering functions**
1. Add `getServiceHeading(service)` helper:
```javascript
function getServiceHeading(service) {
  if (!service) return 'Worship Service';
  if (service.liturgical_day && service.liturgical_day.trim()) {
    return service.liturgical_day.trim();
  }
  const dateStr = service.service_date ? service.service_date.trim() : '';
  const settingStr = service.setting_preset ? service.setting_preset.trim() : '';
  if (dateStr && settingStr) {
    return `${dateStr} • ${settingStr}`;
  }
  return dateStr || settingStr || 'Worship Service';
}
```
2. Update `renderService(service)`:
```javascript
  const heading = getServiceHeading(service);
  const subtitle = `Date: ${service.service_date || '--'} | Setting: ${service.setting_preset || '--'}`;
  document.getElementById('service-title-display').textContent = heading;
  document.getElementById('service-subtitle-display').textContent = subtitle;
```
3. Update `renderMobileServiceInfo()`:
```javascript
  if (!mobileService) return;
  const heading = getServiceHeading(mobileService);
  const baseSubtitle = `Date: ${mobileService.service_date || '--'} | Setting: ${mobileService.setting_preset || '--'}`;
  const modeBadge = (currentMobileUiMode === MOBILE_UI_MODE.HYMNS_ONLY) ? ' • Hymns Only' : ' • Liturgy';
  const titleEl = document.getElementById('mobile-service-title');
  const subEl = document.getElementById('mobile-service-subtitle');
  if (titleEl) titleEl.textContent = heading;
  if (subEl) subEl.textContent = baseSubtitle + modeBadge;
```
4. Update `createDraftServiceLocally()`:
   - Change `title: "Sunday Worship Service"` to `title: dayVal || "Worship Service"`.
5. Update `saveActiveServiceUI()`:
   - Ensure default title uses `currentService.liturgical_day || currentService.title || "Worship Service"`.
6. Update `buildServiceOptionsHtml(services, selectedId)`:
```javascript
  return services.map(s => {
    const isSel = String(s.id) === String(selectedId) ? 'selected' : '';
    const heading = escapeHtml(getServiceHeading(s));
    const dateStr = s.service_date || 'No Date';
    return `<option value="${s.id}" ${isSel}>${dateStr} • ${heading}</option>`;
  }).join('');
```
7. Update `renderServicesExplorerList()`:
```javascript
  filtered.forEach(s => {
    const card = document.createElement('div');
    card.className = 'explorer-card';
    const heading = escapeHtml(getServiceHeading(s));
    card.innerHTML = `
      <div class="flex-between">
        <span class="badge">${s.service_date}</span>
        <span class="subtitle">${s.setting_preset}</span>
      </div>
      <div style="font-weight: 700; color: white;">${heading}</div>
      <div style="font-size: 0.75rem; color: #94a3b8;">Date: ${s.service_date || '--'} | Setting: ${s.setting_preset || '--'}</div>
      <div class="flex-between" style="margin-top: 8px;">
        <button class="btn btn-primary btn-sm" onclick="loadServiceFromExplorer(${s.id})">📂 Open</button>
        <div style="display: flex; gap: 4px;">
          <button class="btn btn-primary btn-sm" onclick="duplicateServiceFromExplorer(${s.id})" title="Duplicate">📋</button>
          <button class="btn-danger-text" onclick="deleteServiceFromExplorer(${s.id})" title="Delete">🗑️</button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
```
8. Update `import-plan-modal`:
   - Set `#import-modal-title` to `getServiceHeading(pendingImportPlanData)` or `plan.liturgical_day || 'Worship Service'`.

**Step 2: Run test suite to verify tests pass**

Run: `python -c "import subprocess; res = subprocess.run(['pytest', 'tests/test_elevate_liturgical_day.py', '-v'], capture_output=True, text=True); print(res.stdout); print(res.stderr)"`  
Expected: PASS.

**Step 3: Commit**

```bash
git add src/static/app.js
git commit -m "feat(ui): elevate liturgical day into primary heading and remove service title"
```

---

### Task 4: Full Suite Regression Verification & Manual Sanity Check

**Files:**
- Verify: Full pytest test suite (`tests/`)

**Step 1: Run all existing tests**

Run: `python -c "import subprocess; res = subprocess.run(['pytest', '-v'], capture_output=True, text=True); print(res.stdout); print(res.stderr)"`  
Expected: All tests pass without regressions.

**Step 2: Commit any test adjustments or final cleanup**

```bash
git status
```
(Commit if necessary).

---
