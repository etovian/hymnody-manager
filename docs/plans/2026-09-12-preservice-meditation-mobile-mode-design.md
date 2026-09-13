# Design Specification: Preservice Meditation Hymns Mode in Sanctuary Mobile UI

**Date**: 2026-09-12  
**Status**: Approved  
**Target Component**: Sanctuary Mobile UI (`src/static/index.html`, `src/static/app.js`, `src/static/styles.css`)

---

## 1. Overview

The Sanctuary Mobile Mode provides a streamlined, high-contrast touch interface designed for church volunteers operating sanctuary audio. This specification introduces **Preservice Meditation Mode** alongside standard **Service Mode** in the mobile UI.

While mid-service playback requires stopping after each track (`SINGLE` playback mode), preservice playback filters the playlist to display **hymns only**, automatically advancing from track to track and looping continuously (`REPEAT_ALL` playback mode) until stopped or toggled back to full service mode.

---

## 2. Playback Architecture & State Enums

### Enums & State Management

1. **`PLAYBACK_MODE`**:
   - `SINGLE`: Plays 1 track and stops on completion (Default for Mid-Service).
   - `CONTINUOUS`: Auto-advances sequentially through active list without looping.
   - `REPEAT_ALL`: Auto-advances through active list and loops back to track 1 upon reaching the end (Default for Preservice).

2. **`MOBILE_UI_MODE`**:
   - `SERVICE`: Full service view (all liturgy & hymn slots displayed). `PLAYBACK_MODE = SINGLE`.
   - `PRESERVICE`: Hymns-only view (filters out liturgical ordinaries). `PLAYBACK_MODE = REPEAT_ALL`.

3. **Global State Variables (`src/static/app.js`)**:
   - `currentPlaybackMode`: Stores active `PLAYBACK_MODE` value (`SINGLE` by default).
   - `currentMobileUiMode`: Stores active `MOBILE_UI_MODE` value (`SERVICE` by default).

---

## 3. Mobile UI & Header Integration

### Header Toggle Button

In `#mobile-view`, a mode toggle button sits inline to the right of `#mobile-service-select` in a single-row flex container:

```html
<div class="mobile-header-controls" style="display: flex; gap: 8px; align-items: center; margin-top: 8px;">
  <select id="mobile-service-select" class="mobile-service-select" style="flex: 1;" ...></select>
  <button id="btn-mobile-mode-toggle" class="btn btn-emerald btn-preservice-pill" onclick="toggleMobileUiMode()">
    📜 Full Service
  </button>
</div>
```

### Visual States & Labels

- **`SERVICE` Mode (Default)**:
  - Button text: `📜 Full Service`
  - Style: Standard high-contrast pill button.
  - Subtitle: `Divine Service Setting Two • Full Service`
- **`PRESERVICE` Mode**:
  - Button text: `🎵 Preservice`
  - Style: Amber/Gold high-contrast active pill with subtle highlight.
  - Subtitle: `Preservice Meditation (4 Hymns) • Looping`

---

## 4. Playlist Filtering & Playback Execution

### Playlist Filtering (`renderMobilePlaylist`)

- In **`SERVICE` Mode**: Renders all `mobileService.items` (liturgy + hymns).
- In **`PRESERVICE` Mode**: Filters rendered list to items where category is `'Hymn'` and audio file exists:
  ```js
  const displayItems = (currentMobileUiMode === MOBILE_UI_MODE.PRESERVICE)
    ? items.filter(item => getTrackCategoryBadge(item).text === 'Hymn' && item.file_path)
    : items;
  ```

### Audio `ended` Event Handler

```js
audioPlayer.addEventListener('ended', () => {
  if (currentPlaybackMode === PLAYBACK_MODE.SINGLE) {
    isPlaying = false;
    audioPlayer.currentTime = 0;
    updatePlayButtonUI();
  } else if (currentPlaybackMode === PLAYBACK_MODE.REPEAT_ALL) {
    const activeItems = getActiveDisplayItems();
    const currentPos = activeItems.findIndex(it => it.index === activeTrackIndex);
    const nextPos = (currentPos + 1) % activeItems.length;

    if (activeItems.length > 0) {
      playServiceTrack(activeItems[nextPos].index);
    } else {
      isPlaying = false;
      updatePlayButtonUI();
    }
  }
});
```

### Mode Transition Rules

- **Switching `SERVICE` → `PRESERVICE`**: Sets `currentMobileUiMode = PRESERVICE`, `currentPlaybackMode = REPEAT_ALL`, and re-renders playlist showing hymns only. If currently playing a hymn, it continues playing. If currently playing a liturgy track, playback pauses.
- **Switching `PRESERVICE` → `SERVICE`**: Sets `currentMobileUiMode = SERVICE`, `currentPlaybackMode = SINGLE`, and re-renders full playlist. Active playing track continues until completion, then stops.

---

## 5. Verification & Testing Strategy

1. **Unit & Integration Tests**:
   - Verify `PLAYBACK_MODE` transitions when toggling `MOBILE_UI_MODE`.
   - Verify hymn filtering logic returns only items with valid audio.
   - Verify wrap-around index calculation for single-hymn and multi-hymn playlists.
2. **Manual UI Verification**:
   - Verify zero vertical screen space added to header in Mobile view.
   - Verify seamless auto-advance and looping in Preservice Mode.
   - Verify single-track stop behavior in Full Service Mode.
