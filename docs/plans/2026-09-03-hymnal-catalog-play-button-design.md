# Design Spec: Hymnal Catalog & Template Editor "Play" Button

**Date:** 2026-09-03  
**Status:** Approved  

## Overview
Replace the `+ Add` button with a `▶ Play` button in both the main Hymnal Catalog list and the Template Editor modal catalog search list. Users add hymns to services and templates using drag-and-drop, making the `+ Add` button superfluous and replacing it with direct audio playback.

## Proposed Changes

### 1. Frontend Audio Playback (`src/static/app.js`)
- Add helper function `playCatalogHymn(hymnId)`:
  - Fetches or retrieves hymn object by `hymnId`.
  - Sets `audioPlayer.src = '/api/hymns/' + hymnId + '/audio'`.
  - Begins audio playback (`audioPlayer.play()`).
  - Sets `isPlaying = true` and `activeTrackIndex = -1`.
  - Updates player UI with track title and season/disc information.

### 2. Main Catalog UI (`renderHymnList`)
- Replace `<button class="btn btn-primary" onclick="handleCatalogAddClick(${h.id})">+ Add</button>`
- With `<button class="btn btn-primary" onclick="playCatalogHymn(${h.id})">▶ Play</button>`

### 3. Template Editor Modal UI (`searchModalCatalog`)
- Replace `<button ... onclick="handleCatalogAddClick(${h.id})">+ Add</button>`
- With `<button ... onclick="playCatalogHymn(${h.id})">▶ Play</button>`

### 4. Drag & Drop Behavior
- Retain full HTML5 drag-and-drop support (`draggable="true"`, `onHymnDragStart`) for dragging catalog tracks into service plan slots or template editor slot rows.

## Verification & Testing
- Automated test in `tests/test_e2e.py` verifying catalog rendering includes `▶ Play` buttons.
- Execute full test suite `pytest -v`.
