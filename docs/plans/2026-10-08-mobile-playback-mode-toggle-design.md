# Design Specification: Mobile Playback Mode Toggle & Services Explorer Integration

## Overview

This specification details the enhancement of the Sanctuary Mobile UI in Hymnody Manager. It introduces an independent playback mode toggle control, updates the playlist filter toggle terminology to align with "Liturgy" vs "Hymns Only", replaces the redundant mobile `<select>` dropdown with a direct launch button for the Services Explorer modal, and ensures live bidirectional synchronization between playlist filter state and playback modes.

---

## 1. State Model & Enums

### 1.1 Enumerations
In `src/static/app.js`:

```javascript
const PLAYBACK_MODE = {
  SINGLE: 'SINGLE',
  CONTINUOUS: 'CONTINUOUS',
  REPEAT_ALL: 'REPEAT_ALL'
};

const MOBILE_UI_MODE = {
  LITURGY: 'LITURGY',
  HYMNS_ONLY: 'HYMNS_ONLY'
};
```

### 1.2 State Variables
- `currentPlaybackMode`: Default is `PLAYBACK_MODE.SINGLE`.
- `currentMobileUiMode`: Default is `MOBILE_UI_MODE.LITURGY`.

### 1.3 State Transitions & Automation
- **Playlist Filter Toggle (`toggleMobileUiMode()`)**:
  - Switching to `HYMNS_ONLY`:
    - `currentMobileUiMode = MOBILE_UI_MODE.HYMNS_ONLY`
    - `currentPlaybackMode = PLAYBACK_MODE.REPEAT_ALL`
  - Switching to `LITURGY`:
    - `currentMobileUiMode = MOBILE_UI_MODE.LITURGY`
    - `currentPlaybackMode = PLAYBACK_MODE.SINGLE`
  - Automatically updates both the filter button (`updateMobileHeaderModeButton()`) and playback mode button (`updateMobilePlaybackModeButton()`).
- **Manual Playback Mode Toggle (`cyclePlaybackMode()`)**:
  - Cycles forward through:
    `SINGLE` &rarr; `CONTINUOUS` &rarr; `REPEAT_ALL` &rarr; `SINGLE`.
  - Updates the button display via `updateMobilePlaybackModeButton()`.
  - Emits a brief toast notifying the operator of the active playback behavior.
  - Does **not** reset the active track or disrupt currently playing audio.

---

## 2. Sanctuary Mobile UI Header Controls

### 2.1 Action Bar Layout
The redundant `<select id="mobile-service-select">` dropdown is replaced by a responsive 3-button action grid located directly beneath the service title and subtitle:

```html
<div class="mobile-header-controls" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px;">
  <button id="btn-mobile-services-explorer" class="btn btn-secondary mobile-header-btn" onclick="openServicesExplorer()">
    📂 Services
  </button>
  <button id="btn-mobile-mode-toggle" class="btn btn-emerald mobile-header-btn" onclick="toggleMobileUiMode()">
    📜 Liturgy
  </button>
  <button id="btn-mobile-playback-mode" class="btn btn-primary mobile-header-btn" onclick="cyclePlaybackMode()">
    ⏹ Single Track
  </button>
</div>
```

### 2.2 Button States & Styling
1. **Services Button (`btn-mobile-services-explorer`)**:
   - Class: `btn btn-secondary mobile-header-btn`
   - Action: Calls `openServicesExplorer()`, reusing the Desktop Planner's Services Explorer modal (search, upcoming/past filter tabs, date chips).
   - When a service is selected via `loadServiceFromExplorer()`, the mobile view automatically loads and re-renders the new service.

2. **Playlist Filter Button (`btn-mobile-mode-toggle`)**:
   - When `currentMobileUiMode === MOBILE_UI_MODE.LITURGY`:
     - Label: `📜 Liturgy`
     - Class: `btn btn-emerald mobile-header-btn`
   - When `currentMobileUiMode === MOBILE_UI_MODE.HYMNS_ONLY`:
     - Label: `🎵 Hymns Only`
     - Class: `btn btn-preservice-pill btn-preservice-active mobile-header-btn`

3. **Playback Mode Button (`btn-mobile-playback-mode`)**:
   - When `currentPlaybackMode === PLAYBACK_MODE.SINGLE`:
     - Label: `⏹ Single Track`
     - Class: `btn btn-slate mobile-header-btn`
   - When `currentPlaybackMode === PLAYBACK_MODE.CONTINUOUS`:
     - Label: `⏩ Continuous`
     - Class: `btn btn-amber mobile-header-btn`
   - When `currentPlaybackMode === PLAYBACK_MODE.REPEAT_ALL`:
     - Label: `🔁 Repeat All`
     - Class: `btn btn-blue mobile-header-btn`

---

## 3. Audio Advancement Logic

Inside the `audioPlayer.addEventListener('ended')` handler in `src/static/app.js`:

1. **`PLAYBACK_MODE.SINGLE`**:
   - Halts playback: `isPlaying = false`.
   - Resets playhead: `audioPlayer.currentTime = 0`.
   - Refreshes UI buttons and playlist item states.

2. **`PLAYBACK_MODE.CONTINUOUS`**:
   - Resolves active display items from `getActiveDisplayItems()`.
   - Determines current track position in the filtered list.
   - If `currentPos + 1 < activeItems.length`, plays `activeItems[currentPos + 1]`.
   - If already at the last track (`currentPos === activeItems.length - 1`), halts playback without looping.

3. **`PLAYBACK_MODE.REPEAT_ALL`**:
   - Resolves active display items.
   - Computes `nextPos = (currentPos + 1) % activeItems.length`.
   - Auto-plays `activeItems[nextPos]`, repeating seamlessly indefinitely.

---

## 4. Verification & Testing Plan

1. **State & Enum Tests**:
   - Verify `PLAYBACK_MODE` contains `SINGLE`, `CONTINUOUS`, and `REPEAT_ALL`.
   - Verify `MOBILE_UI_MODE` contains `LITURGY` and `HYMNS_ONLY`.
2. **Cycle & Sync Behavior**:
   - Test cycling through all 3 modes sequentially with `cyclePlaybackMode()`.
   - Test automatic updates to playback mode and button presentation when `toggleMobileUiMode()` is invoked.
3. **DOM & Action Bar Verification**:
   - Verify presence of `btn-mobile-services-explorer`, `btn-mobile-mode-toggle`, and `btn-mobile-playback-mode`.
   - Verify removal or deprecation of `mobile-service-select`.
4. **Pytest Suite Execution**:
   - Run `python -m pytest -v` across all test suites to confirm zero regressions.
