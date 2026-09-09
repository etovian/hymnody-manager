# Sanctuary Mobile Mode UI Redesign Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign Sanctuary Mobile Mode UI to eliminate vertical clutter by compacting the top application header and replacing the standalone "Now Playing" box with inline expandable player controls inside the active playlist track card.

**Architecture:** 
1. Header compacting via CSS state class `.mobile-mode-active` triggered on `switchView('mobile')`.
2. Removal of `.now-playing-box` HTML element from `#mobile-view`.
3. Dynamic rendering of active vs inactive track cards in `app.js`'s `renderMobilePlaylist()`, featuring an expanded active card with scrubber, timestamps, play/pause, and restart track controls.

**Tech Stack:** HTML5, CSS3, Vanilla JavaScript (ES6+), Pytest for test suite.

---

## User Review Required

> [!IMPORTANT]
> - Standing rule: Pausing for review before making code changes.
> - Git branch `feature/mobile-ui-redesign` has been created for work isolation.
> - No breaking backend API changes; strictly frontend HTML/CSS/JS enhancements.

---

## Proposed Tasks

### Task 1: HTML Restructuring & Standalone Box Removal

**Files:**
- Modify: `src/static/index.html:174-207`

**Steps:**
1. Remove `.now-playing-box` container from `<section id="mobile-view">`.
2. Simplify `.mobile-header` to compact the service title and dropdown selector.
3. Ensure `#mobile-playlist-container` is structured for dynamic inline expansion cards.

---

### Task 2: CSS Styling for Compact Header & Inline Active Track Player

**Files:**
- Modify: `src/static/styles.css`

**Steps:**
1. Add `.mobile-mode-active` rules for `.header`:
   - Hide subtitle (`.header .subtitle`).
   - Compact brand logo (`.brand-logo`) and title (`.title`).
   - Style view switch buttons as a compact pill container in mobile view.
2. Add inline player styles:
   - `.mobile-track-card` (inactive card, compact single line).
   - `.mobile-track-card.active-track-card` (highlighted border, glowing background).
   - `.inline-player-controls` (accordion container with max-height transition).
   - `.mobile-inline-scrubber` (touch-friendly range input).
   - Button styles for `.btn-mobile-play-pause` and `.btn-mobile-restart`.

---

### Task 3: JavaScript Application Logic for Inline Expansion & Header Toggle

**Files:**
- Modify: `src/static/app.js`

**Steps:**
1. Update `switchView(mode)`:
   - Toggle `.mobile-mode-active` class on the header element based on `mode === 'mobile'`.
2. Refactor `renderMobilePlaylist(service)`:
   - For each track item, check if `index === activeTrackIndex`.
   - If active, generate the expanded card template containing title, subtitle, live status badge (`▶ PLAYING` / `⏸ PAUSED`), scrubber input, timestamps (`0:00`), play/pause button, and restart button.
   - If inactive, generate compact single-row item with tap-to-play click handler.
3. Update `setupAudioListeners()`:
   - On `timeupdate`: update `#mobile-inline-scrubber`, `#mobile-inline-current`, and `#mobile-inline-total` on the active card.
   - On `ended`: auto-advance to next track, triggering smooth collapse of current card and expansion of next card.
4. Add inline event handlers:
   - `toggleMobilePlayPause()`: toggles audio play/pause state.
   - `restartCurrentTrack()`: rewinds `audioPlayer.currentTime = 0`.
   - `seekAudioMobile(value)`: seeks audio position.

---

### Task 4: Testing & Verification

**Files:**
- Test: `tests/test_e2e.py`
- Test: `tests/test_api.py`

**Steps:**
1. Run automated test suite: `pytest -v`.
2. Verify all 58 existing unit & integration tests pass cleanly.
3. Validate HTML syntax and asset references.
