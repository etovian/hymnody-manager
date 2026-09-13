# Preservice Meditation Mobile Mode Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Preservice Meditation mode toggle to the Sanctuary Mobile UI that filters the playlist to hymns only and continuously loops playback (`REPEAT_ALL`), while maintaining single-track stop behavior (`SINGLE`) for mid-service worship.

**Architecture:** Introduce `PLAYBACK_MODE` and `MOBILE_UI_MODE` state constants in JavaScript (`src/static/app.js`), add an inline mode toggle button to the mobile header (`src/static/index.html`), update playlist filtering in `renderMobilePlaylist()`, and update the audio `ended` event handler to auto-advance and wrap around in `REPEAT_ALL` mode.

**Tech Stack:** Vanilla JavaScript (ES6+), HTML5, CSS3, Python / Pytest for test suite.

---

### Task 1: Add State Enums and Helper Functions in `src/static/app.js`

**Files:**
- Modify: `src/static/app.js:20-50`
- Test: `tests/test_mobile_preservice.py`

**Step 1: Write the failing test**

Create `tests/test_mobile_preservice.py`:
```python
import pytest

def test_mobile_mode_constants_present():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "const PLAYBACK_MODE" in content
    assert "SINGLE: 'SINGLE'" in content
    assert "REPEAT_ALL: 'REPEAT_ALL'" in content
    assert "const MOBILE_UI_MODE" in content
    assert "SERVICE: 'SERVICE'" in content
    assert "PRESERVICE: 'PRESERVICE'" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mobile_preservice.py -v`  
Expected: FAIL with missing assertion `const PLAYBACK_MODE` in content.

**Step 3: Write minimal implementation**

Modify `src/static/app.js` at the top near state definitions:
```javascript
const PLAYBACK_MODE = {
  SINGLE: 'SINGLE',
  CONTINUOUS: 'CONTINUOUS',
  REPEAT_ALL: 'REPEAT_ALL'
};

const MOBILE_UI_MODE = {
  SERVICE: 'SERVICE',
  PRESERVICE: 'PRESERVICE'
};

let currentPlaybackMode = PLAYBACK_MODE.SINGLE;
let currentMobileUiMode = MOBILE_UI_MODE.SERVICE;

function getActiveDisplayItems() {
  const items = mobileService ? (mobileService.items || []) : [];
  if (currentMobileUiMode === MOBILE_UI_MODE.PRESERVICE) {
    return items.filter(item => {
      const badge = getTrackCategoryBadge(item, Boolean(item.file_path && item.file_path.trim()));
      return badge.text === 'Hymn' && Boolean(item.file_path && item.file_path.trim());
    });
  }
  return items;
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_mobile_preservice.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_mobile_preservice.py src/static/app.js
git commit -m "feat: add PLAYBACK_MODE and MOBILE_UI_MODE state enums and helpers"
```

---

### Task 2: Add Header Toggle Button in `src/static/index.html` & CSS Styling

**Files:**
- Modify: `src/static/index.html:193-200`
- Modify: `src/static/styles.css:250-280`
- Test: `tests/test_mobile_preservice.py`

**Step 1: Write the failing test**

Add test function to `tests/test_mobile_preservice.py`:
```python
def test_mobile_header_toggle_button_present():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert 'id="btn-mobile-mode-toggle"' in html
    assert 'toggleMobileUiMode()' in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert '.mobile-header-controls' in css
    assert '.btn-preservice-pill' in css
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mobile_preservice.py::test_mobile_header_toggle_button_present -v`  
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `src/static/index.html`:
```html
<div class="mobile-header">
  <h2 id="mobile-service-title" style="font-size: 1.5rem; font-weight: 800; color: white;">Sunday Worship Service</h2>
  <p id="mobile-service-subtitle" class="subtitle">Divine Service Setting Two</p>
  <div class="mobile-header-controls" style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
    <select id="mobile-service-select" class="mobile-service-select" aria-label="Select Worship Service" onchange="onMobileServiceSelectChanged(this.value)" style="flex: 1; margin: 0;"></select>
    <button id="btn-mobile-mode-toggle" class="btn btn-emerald btn-preservice-pill" onclick="toggleMobileUiMode()" style="white-space: nowrap; padding: 10px 14px; font-weight: 700; border-radius: 8px; font-size: 0.85rem;">
      📜 Full Service
    </button>
  </div>
</div>
```

Modify `src/static/styles.css`:
```css
.mobile-header-controls {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  width: 100%;
}

.btn-preservice-pill {
  white-space: nowrap;
  padding: 10px 14px;
  font-weight: 700;
  border-radius: 8px;
  font-size: 0.85rem;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.btn-preservice-active {
  background: linear-gradient(135deg, #d97706, #b45309) !important;
  color: #ffffff !important;
  border: 1px solid #f59e0b !important;
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_mobile_preservice.py::test_mobile_header_toggle_button_present -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/static/index.html src/static/styles.css tests/test_mobile_preservice.py
git commit -m "feat: add inline preservice mode toggle button to mobile header"
```

---

### Task 3: Implement Mode Toggle and Playlist Filtering Logic in `src/static/app.js`

**Files:**
- Modify: `src/static/app.js:1540-1640`
- Test: `tests/test_mobile_preservice.py`

**Step 1: Write the failing test**

Add test function to `tests/test_mobile_preservice.py`:
```python
def test_toggle_mobile_ui_mode_function_present():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "function toggleMobileUiMode()" in content
    assert "currentMobileUiMode = MOBILE_UI_MODE.PRESERVICE" in content
    assert "currentPlaybackMode = PLAYBACK_MODE.REPEAT_ALL" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mobile_preservice.py::test_toggle_mobile_ui_mode_function_present -v`  
Expected: FAIL

**Step 3: Write minimal implementation**

In `src/static/app.js`:
```javascript
function toggleMobileUiMode() {
  if (currentMobileUiMode === MOBILE_UI_MODE.SERVICE) {
    currentMobileUiMode = MOBILE_UI_MODE.PRESERVICE;
    currentPlaybackMode = PLAYBACK_MODE.REPEAT_ALL;
    showToast("Preservice Meditation Mode (Hymns Only • Looping)", "info", "Preservice Mode");
  } else {
    currentMobileUiMode = MOBILE_UI_MODE.SERVICE;
    currentPlaybackMode = PLAYBACK_MODE.SINGLE;
    showToast("Full Service Mode (Single Track Stop)", "info", "Service Mode");
  }

  updateMobileHeaderModeButton();
  renderMobileServiceInfo();
  renderMobilePlaylist();
}

function updateMobileHeaderModeButton() {
  const btn = document.getElementById('btn-mobile-mode-toggle');
  if (!btn) return;

  if (currentMobileUiMode === MOBILE_UI_MODE.PRESERVICE) {
    btn.textContent = '🎵 Preservice';
    btn.className = 'btn btn-preservice-pill btn-preservice-active';
  } else {
    btn.textContent = '📜 Full Service';
    btn.className = 'btn btn-emerald btn-preservice-pill';
  }
}
```

Update `renderMobileServiceInfo()`:
```javascript
function renderMobileServiceInfo() {
  if (!mobileService) return;
  const baseSubtitle = `${mobileService.service_date || ''}${mobileService.liturgical_day ? ' • ' + mobileService.liturgical_day : ''} | Setting: ${mobileService.setting_preset || ''}`;
  const modeBadge = (currentMobileUiMode === MOBILE_UI_MODE.PRESERVICE) ? ' • Preservice Hymns (Looping)' : ' • Full Service';
  const titleEl = document.getElementById('mobile-service-title');
  const subEl = document.getElementById('mobile-service-subtitle');
  if (titleEl) titleEl.textContent = mobileService.title || 'Sunday Service';
  if (subEl) subEl.textContent = baseSubtitle + modeBadge;
}
```

Update `renderMobilePlaylist()`:
```javascript
function renderMobilePlaylist(service = mobileService) {
  const mobilePlaylist = document.getElementById('mobile-playlist-container');
  if (!mobilePlaylist) return;
  mobilePlaylist.innerHTML = '';

  const items = getActiveDisplayItems();
  if (items.length === 0) {
    const msg = (currentMobileUiMode === MOBILE_UI_MODE.PRESERVICE)
      ? 'No hymns with audio files available in this service plan.'
      : 'No service selected or service has no items.';
    mobilePlaylist.innerHTML = `<div style="color: #94a3b8; font-size: 0.9rem; padding: 1rem; text-align: center;">${msg}</div>`;
    return;
  }

  items.forEach((item, displayIdx) => {
    const originalIndex = (mobileService && mobileService.items) ? mobileService.items.indexOf(item) : displayIdx;
    const indexToUse = originalIndex !== -1 ? originalIndex : displayIdx;

    const hasAudio = Boolean(item.file_path && item.file_path.trim());
    const isActive = (indexToUse === activeTrackIndex);
    const displayTitle = item.item_title || item.title || item.slot_name || `Track ${displayIdx + 1}`;
    const displaySlot = getDisplaySlot(item, displayTitle);

    // Render track card (active vs inactive) calling onMobileTrackClicked(indexToUse)
    // ...
  });
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_mobile_preservice.py::test_toggle_mobile_ui_mode_function_present -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/static/app.js tests/test_mobile_preservice.py
git commit -m "feat: implement mobile mode toggling and playlist filtering"
```

---

### Task 4: Update Audio `ended` Event Listener for `SINGLE` vs `REPEAT_ALL`

**Files:**
- Modify: `src/static/app.js:1820-1850`
- Test: `tests/test_mobile_preservice.py`

**Step 1: Write the failing test**

Add test function to `tests/test_mobile_preservice.py`:
```python
def test_ended_event_listener_uses_playback_mode():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "PLAYBACK_MODE.REPEAT_ALL" in content
    assert "getActiveDisplayItems()" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mobile_preservice.py::test_ended_event_listener_uses_playback_mode -v`  
Expected: FAIL

**Step 3: Write minimal implementation**

In `src/static/app.js` inside `setupAudioListeners()`:
```javascript
  audioPlayer.addEventListener('ended', () => {
    if (currentPlaybackMode === PLAYBACK_MODE.SINGLE) {
      isPlaying = false;
      audioPlayer.currentTime = 0;
      updatePlayButtonUI();
      renderMobilePlaylist();
    } else if (currentPlaybackMode === PLAYBACK_MODE.REPEAT_ALL) {
      const activeItems = getActiveDisplayItems();
      if (activeItems.length > 0) {
        let currentPos = activeItems.findIndex(it => {
          if (mobileService && mobileService.items) {
            return mobileService.items.indexOf(it) === activeTrackIndex;
          }
          return false;
        });
        if (currentPos === -1) currentPos = 0;
        const nextPos = (currentPos + 1) % activeItems.length;
        const nextItem = activeItems[nextPos];
        const nextIndex = (mobileService && mobileService.items) ? mobileService.items.indexOf(nextItem) : 0;
        playServiceTrack(nextIndex);
      } else {
        isPlaying = false;
        audioPlayer.currentTime = 0;
        updatePlayButtonUI();
        renderMobilePlaylist();
      }
    }
  });
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_mobile_preservice.py -v`  
Expected: PASS (All tests passing)

**Step 5: Commit**

```bash
git add src/static/app.js tests/test_mobile_preservice.py
git commit -m "feat: handle auto-advance and wrap-around looping in REPEAT_ALL mode"
```

---

### Task 5: Full Test Suite & Verification

**Step 1: Run complete pytest test suite**

Run: `pytest -v`  
Expected: All tests pass (60+ tests passing).

**Step 2: Final Commit**

```bash
git add .
git commit -m "test: verify preservice meditation mobile mode implementation"
```
