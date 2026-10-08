# Mobile Playback Mode Toggle & Services Explorer Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance Sanctuary Mobile UI with an independent 3-way playback mode toggle (`Single Track` / `Continuous` / `Repeat All`), synchronize its display with playlist mode transitions ("Liturgy" vs "Hymns Only"), and replace the redundant mobile service dropdown with a Services Explorer launch button.

**Architecture:** Maintain unidirectional and synchronized state in `src/static/app.js` using `PLAYBACK_MODE` (`SINGLE`, `CONTINUOUS`, `REPEAT_ALL`) and `MOBILE_UI_MODE` (`LITURGY`, `HYMNS_ONLY`). Add `cyclePlaybackMode()` and `updateMobilePlaybackModeButton()` to keep the UI in sync whenever the mode changes manually or via filter toggle. Implement sequential stop-at-end behavior for `CONTINUOUS` mode in the HTML5 audio `ended` event listener. Add a responsive 3-button touch toolbar in `src/static/index.html` and style with distinct state badges in `src/static/styles.css`.

**Tech Stack:** Vanilla JavaScript (ES6+), HTML5, CSS3, Python / FastAPI, Pytest.

---

### Task 1: Update State Enums & Add Playback Mode Cycle Logic in `src/static/app.js`

**Files:**
- Modify: `src/static/app.js:21-46`
- Modify: `src/static/app.js:2053-2080`
- Test: `tests/test_mobile_playback_mode.py`

**Step 1: Write the failing test**
Create `tests/test_mobile_playback_mode.py`:
```python
import pytest

def test_playback_mode_and_mobile_ui_mode_enums():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    # PLAYBACK_MODE enum
    assert "const PLAYBACK_MODE" in content
    assert "SINGLE: 'SINGLE'" in content
    assert "CONTINUOUS: 'CONTINUOUS'" in content
    assert "REPEAT_ALL: 'REPEAT_ALL'" in content

    # MOBILE_UI_MODE enum
    assert "const MOBILE_UI_MODE" in content
    assert "LITURGY: 'LITURGY'" in content
    assert "HYMNS_ONLY: 'HYMNS_ONLY'" in content

def test_cycle_playback_mode_and_button_updater_defined():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    assert "function cyclePlaybackMode()" in content
    assert "function updateMobilePlaybackModeButton()" in content
    assert "updateMobilePlaybackModeButton()" in content
```

**Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_mobile_playback_mode.py -v`
Expected: FAIL with missing `LITURGY: 'LITURGY'` or `cyclePlaybackMode()`.

**Step 3: Implement minimal state updates and functions**
In `src/static/app.js`:
1. Update `PLAYBACK_MODE` and `MOBILE_UI_MODE`:
   ```javascript
   const PLAYBACK_MODE = {
     SINGLE: 'SINGLE',
     CONTINUOUS: 'CONTINUOUS',
     REPEAT_ALL: 'REPEAT_ALL'
   };

   const MOBILE_UI_MODE = {
     LITURGY: 'LITURGY',
     HYMNS_ONLY: 'HYMNS_ONLY',
     // Backward compatibility aliases
     SERVICE: 'LITURGY',
     PRESERVICE: 'HYMNS_ONLY'
   };

   let currentPlaybackMode = PLAYBACK_MODE.SINGLE;
   let currentMobileUiMode = MOBILE_UI_MODE.LITURGY;
   ```
2. Update `getActiveDisplayItems` to check `currentMobileUiMode === MOBILE_UI_MODE.HYMNS_ONLY`.
3. Add `cyclePlaybackMode()`:
   ```javascript
   function cyclePlaybackMode() {
     if (currentPlaybackMode === PLAYBACK_MODE.SINGLE) {
       currentPlaybackMode = PLAYBACK_MODE.CONTINUOUS;
       showToast("Continuous Playback (Plays through end of playlist)", "info", "Playback Mode");
     } else if (currentPlaybackMode === PLAYBACK_MODE.CONTINUOUS) {
       currentPlaybackMode = PLAYBACK_MODE.REPEAT_ALL;
       showToast("Repeat All (Loops playlist continuously)", "info", "Playback Mode");
     } else {
       currentPlaybackMode = PLAYBACK_MODE.SINGLE;
       showToast("Single Track (Stops after each track)", "info", "Playback Mode");
     }
     updateMobilePlaybackModeButton();
   }
   ```
4. Add `updateMobilePlaybackModeButton()`:
   ```javascript
   function updateMobilePlaybackModeButton() {
     const btn = document.getElementById('btn-mobile-playback-mode');
     if (!btn) return;

     if (currentPlaybackMode === PLAYBACK_MODE.CONTINUOUS) {
       btn.textContent = '⏩ Continuous';
       btn.className = 'btn btn-amber mobile-header-btn';
     } else if (currentPlaybackMode === PLAYBACK_MODE.REPEAT_ALL) {
       btn.textContent = '🔁 Repeat All';
       btn.className = 'btn btn-blue mobile-header-btn';
     } else {
       btn.textContent = '⏹ Single Track';
       btn.className = 'btn btn-slate mobile-header-btn';
     }
   }
   ```
5. Update `toggleMobileUiMode()` and `updateMobileHeaderModeButton()`:
   - When entering `HYMNS_ONLY`: `currentPlaybackMode = PLAYBACK_MODE.REPEAT_ALL`.
   - When entering `LITURGY`: `currentPlaybackMode = PLAYBACK_MODE.SINGLE`.
   - Call both `updateMobileHeaderModeButton()` and `updateMobilePlaybackModeButton()`.
   - Update labels in `updateMobileHeaderModeButton()`: `🎵 Hymns Only` (with `.btn-preservice-active`) and `📜 Liturgy` (with `.btn-emerald`).

**Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_mobile_playback_mode.py -v`
Expected: PASS

**Step 5: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js', 'tests/test_mobile_playback_mode.py']); subprocess.run(['git', 'commit', '-m', 'feat: add playback mode cycling and mobile UI mode enums'])"
```

---

### Task 2: Implement Audio `ended` Event Logic for `CONTINUOUS` Mode

**Files:**
- Modify: `src/static/app.js:2375-2415`
- Test: `tests/test_mobile_playback_mode.py`

**Step 1: Write the failing test**
In `tests/test_mobile_playback_mode.py`, add:
```python
def test_audio_ended_handles_continuous_mode():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    assert "PLAYBACK_MODE.CONTINUOUS" in content
    assert "currentPos + 1 < activeItems.length" in content
```

**Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_mobile_playback_mode.py::test_audio_ended_handles_continuous_mode -v`
Expected: FAIL

**Step 3: Update `audioPlayer.addEventListener('ended')` in `src/static/app.js`**
Update ended handler:
```javascript
  audioPlayer.addEventListener('ended', () => {
    if (currentPlaybackMode === PLAYBACK_MODE.SINGLE) {
      isPlaying = false;
      audioPlayer.currentTime = 0;
      updatePlayButtonUI();
      renderMobilePlaylist();
    } else if (currentPlaybackMode === PLAYBACK_MODE.CONTINUOUS) {
      const activeItems = getActiveDisplayItems();
      if (activeItems.length > 0) {
        let currentPos = activeItems.findIndex(it => {
          if (mobileService && mobileService.items) {
            return mobileService.items.indexOf(it) === activeTrackIndex;
          }
          return false;
        });
        if (currentPos !== -1 && currentPos + 1 < activeItems.length) {
          const nextItem = activeItems[currentPos + 1];
          const nextIndex = (mobileService && mobileService.items) ? mobileService.items.indexOf(nextItem) : 0;
          playServiceTrack(nextIndex);
        } else {
          // Reached the end of playlist - stop playback
          isPlaying = false;
          audioPlayer.currentTime = 0;
          updatePlayButtonUI();
          renderMobilePlaylist();
        }
      } else {
        isPlaying = false;
        audioPlayer.currentTime = 0;
        updatePlayButtonUI();
        renderMobilePlaylist();
      }
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
    } else {
      isPlaying = false;
      audioPlayer.currentTime = 0;
      updatePlayButtonUI();
      renderMobilePlaylist();
    }
  });
```

**Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_mobile_playback_mode.py::test_audio_ended_handles_continuous_mode -v`
Expected: PASS

**Step 5: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js', 'tests/test_mobile_playback_mode.py']); subprocess.run(['git', 'commit', '-m', 'feat: handle sequential stop-at-end in CONTINUOUS playback mode'])"
```

---

### Task 3: Update Mobile Header HTML & CSS for 3-Button Action Toolbar

**Files:**
- Modify: `src/static/index.html:195-205`
- Modify: `src/static/styles.css:825-860`
- Test: `tests/test_mobile_playback_mode.py`

**Step 1: Write the failing test**
In `tests/test_mobile_playback_mode.py`, add:
```python
def test_mobile_header_three_button_action_bar_present():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="btn-mobile-services-explorer"' in html
    assert 'onclick="openServicesExplorer()"' in html
    assert 'id="btn-mobile-mode-toggle"' in html
    assert 'id="btn-mobile-playback-mode"' in html
    assert 'onclick="cyclePlaybackMode()"' in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()

    assert '.mobile-header-btn' in css
```

**Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_mobile_playback_mode.py::test_mobile_header_three_button_action_bar_present -v`
Expected: FAIL

**Step 3: Update `src/static/index.html` & `src/static/styles.css`**
1. In `src/static/index.html`:
   Replace the controls row with:
   ```html
   <div class="mobile-header-controls">
     <button id="btn-mobile-services-explorer" class="btn btn-secondary mobile-header-btn" onclick="openServicesExplorer()">
       📂 Services
     </button>
     <button id="btn-mobile-mode-toggle" class="btn btn-emerald mobile-header-btn" onclick="toggleMobileUiMode()">
       📜 Liturgy
     </button>
     <button id="btn-mobile-playback-mode" class="btn btn-slate mobile-header-btn" onclick="cyclePlaybackMode()">
       ⏹ Single Track
     </button>
     <select id="mobile-service-select" class="mobile-service-select hidden" style="display: none;" aria-hidden="true"></select>
   </div>
   ```
2. In `src/static/styles.css`:
   Add styling for `.mobile-header-controls`, `.mobile-header-btn`, `.btn-slate`, `.btn-amber`, `.btn-blue`:
   ```css
   .mobile-header-controls {
     display: grid;
     grid-template-columns: repeat(3, 1fr);
     gap: 8px;
     margin-top: 10px;
   }

   .mobile-header-btn {
     white-space: nowrap;
     padding: 10px 6px;
     font-weight: 700;
     border-radius: 8px;
     font-size: 0.82rem;
     text-align: center;
     justify-content: center;
     min-height: 42px;
   }

   .btn-slate {
     background: #334155;
     color: #f8fafc;
     border: 1px solid #475569;
   }
   .btn-slate:hover {
     background: #475569;
   }

   .btn-amber {
     background: #d97706;
     color: #ffffff;
     border: 1px solid #b45309;
   }
   .btn-amber:hover {
     background: #b45309;
   }

   .btn-blue {
     background: #2563eb;
     color: #ffffff;
     border: 1px solid #1d4ed8;
   }
   .btn-blue:hover {
     background: #1d4ed8;
   }
   ```
3. Initialize the playback button in `initApp()` in `src/static/app.js` by calling `updateMobilePlaybackModeButton()`.

**Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_mobile_playback_mode.py::test_mobile_header_three_button_action_bar_present -v`
Expected: PASS

**Step 5: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/styles.css', 'src/static/app.js', 'tests/test_mobile_playback_mode.py']); subprocess.run(['git', 'commit', '-m', 'feat: add 3-button mobile action toolbar with services explorer and playback mode buttons'])"
```

---

### Task 4: Full Regression Testing & Verification

**Files:**
- Test: `tests/`

**Step 1: Run complete test suite**
Run: `python -m pytest -v`
Expected: PASS (all tests pass, 130+ passing tests).

**Step 2: Commit any final test cleanups or documentation updates**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', '-A']); subprocess.run(['git', 'commit', '-m', 'test: verify mobile playback mode toggle and e2e test suite'])"
```
