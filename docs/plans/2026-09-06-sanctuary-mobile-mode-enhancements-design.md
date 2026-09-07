# Sanctuary Mobile Mode Enhancements — Design Specification

**Date**: 2026-09-06  
**Status**: Validated  
**Target**: `src/static/index.html`, `src/static/app.js`, `src/static/styles.css`

---

## 1. Overview & Objectives

Sanctuary Mobile Mode is designed for non-technical sanctuary operators using touch devices. This enhancement improves mobile usability, visual feedback, service selection autonomy, and vertical screen layout efficiency:

1. **Independent Service Selector**: Sanctuary Mobile Mode will feature a dedicated service dropdown selector decoupled from the Desktop Worship Planner.
2. **Smart Date Defaulting**: On load, Mobile Mode defaults to selecting a service with today's date (`YYYY-MM-DD`). If none exists, it selects the nearest future service, then the most recent past service.
3. **Single-Tap Play/Pause**: Tapping any track item starts playback immediately. Tapping the currently active track toggles between play and pause states.
4. **Distinct Active Track Styling**: The active track features high-contrast visual indicators: a bright blue accent border with a `▶ PLAYING` badge when active/playing, and an amber accent border with a `⏸ PAUSED` badge when active/paused.
5. **Freed Vertical Layout**: The giant control grid (`PREVIOUS`, `PLAY`, `NEXT TRACK` buttons) is removed, freeing up screen real estate for an expanded playlist container.

---

## 2. Architecture & State Management

### 2.1 State Variables (`app.js`)
* `mobileService`: Object representing the currently selected service plan in Sanctuary Mobile Mode (decoupled from `currentService`).
* `mobileActiveTrackIndex`: Integer index of the currently active track item within `mobileService.items`.
* `isPlaying`: Global boolean reflecting audio element playback status.

### 2.2 Reusable Service Selector Helper
A javascript helper `buildServiceOptionsHtml(services, selectedId)` builds formatted `<option>` elements:
```javascript
// Formats: "YYYY-MM-DD • Title (Setting)"
```
This is shared between the Desktop Planner service selection and Sanctuary Mobile Mode service selection dropdowns.

### 2.3 Smart Date Defaulting Algorithm
When populating or initializing Sanctuary Mobile Mode:
1. Today's ISO Date (`todayStr = new Date().toISOString().split('T')[0]`).
2. Exact Match: Find service with `service_date === todayStr`.
3. Nearest Future: If none, find service with `service_date > todayStr`, sorted ascending by date (smallest future date).
4. Most Recent Past: If none, find service with `service_date < todayStr`, sorted descending by date (largest past date).
5. Load the target service into `mobileService` and render the playlist.

---

## 3. UI Layout & Component Changes

### 3.1 `index.html` Changes
* Remove `.giant-controls-grid` (`PREVIOUS`, `PLAY`, `NEXT TRACK` buttons).
* Add `#mobile-service-select` `<select>` element in `.mobile-header` for independent service picking.
* Retain `#mobile-view` Now Playing header card (track title, slot name, progress bar, scrubber, elapsed/total time).
* Expand `#mobile-playlist-container` height to maximize visible playlist items.

### 3.2 Playlist Item Tap Interaction (`app.js`)
Function `toggleMobileTrack(index)` handles track clicks:
* **Unbound Track**: Shows error toast if `item.file_path` is missing.
* **New Track (`index !== mobileActiveTrackIndex`)**: Updates active index, loads track URL `/api/stream/{file_path}`, starts playback (`audioPlayer.play()`), sets `isPlaying = true`.
* **Active Track & Playing**: Calls `audioPlayer.pause()`, sets `isPlaying = false`.
* **Active Track & Paused**: Calls `audioPlayer.play()`, sets `isPlaying = true`.

### 3.3 CSS Styling Specifications (`styles.css`)
* `.mobile-playlist-item`: Base dark theme card (`#1e293b`).
* `.mobile-playlist-item.active-playing`: 
  * `border: 2px solid #3b82f6` (bright blue accent)
  * `background: #1e3a8a` (tinted blue background)
  * Badge: `<span class="badge-playing">▶ PLAYING</span>`
* `.mobile-playlist-item.active-paused`: 
  * `border: 2px solid #f59e0b` (amber accent)
  * `background: #78350f` (tinted amber background)
  * Badge: `<span class="badge-paused">⏸ PAUSED</span>`

---

## 4. Verification & Testing Strategy

1. **Automated Unit Tests**:
   * Run existing pytest test suite (`pytest -v`) to confirm 58 passing tests without regressions.
2. **Manual Verification**:
   * Launch `uvicorn src.main:app --port 8000`.
   * Verify independent service selection in Mobile Mode header.
   * Verify auto-defaulting logic for current date -> future date -> past date.
   * Verify tap to play / tap to pause behavior on playlist items.
   * Verify high-contrast blue (`▶ PLAYING`) and amber (`⏸ PAUSED`) badges and borders.
