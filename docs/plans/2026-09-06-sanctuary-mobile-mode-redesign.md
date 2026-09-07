# Sanctuary Mobile Mode UI Redesign

**Date**: 2026-09-06  
**Status**: Approved  

---

## 1. Overview & Objectives

The Sanctuary Mobile Mode is designed for church volunteers and pastors operating Lutheran worship audio streaming over Bluetooth or mobile browsers. Feedback from physical device testing indicated that the top application header, service header, and standalone "Now Playing" card occupied ~50% of vertical screen real estate, leaving only 1–2 playlist items visible on screen.

### Key Goals:
1. **Minimize Header Overhead**: Compact the top app header bar ("Hymnody Manager") into an ultra-slim single-line header (`~40px`) when in Mobile Mode.
2. **Inline Active Track Expansion**: Remove the separate standalone "Now Playing" box. Instead, expand the active playlist track card inline to host the progress scrubber bar, timestamps, play/pause controls, and track restart button.
3. **Maximize Playlist Viewport**: Expose 4–6 playlist items on screen simultaneously without sacrificing touch target sizes.

---

## 2. Component Architecture & UI Changes

### 2.1 Compact Header Bar (`.header.mobile-active`)
- When `switchView('mobile')` is triggered, `.mobile-active` is added to `<header class="header">`.
- Subtitle *"Lutheran Worship Planner & Sanctuary Audio Engine"* is hidden.
- Logo and title shrink to `1.0rem` single-line text (`🎼 Hymnody Manager`).
- Desktop/Mobile view switch buttons transition into a compact pill button (`📱 Mobile Mode ▾`) with a dropdown for returning to Desktop Planner mode.

### 2.2 Removal of Standalone "Now Playing" Box
- The static `<div class="now-playing-box">` in `src/static/index.html` is removed from Mobile Mode.
- All playback indicators are consolidated into dynamic playlist item cards rendered inside `#mobile-playlist-container`.

### 2.3 Dynamic Inline Track Card States (`.mobile-track-card`)
- **Inactive Track Card**:
  - Single-line compact row with track number, title, and category badge (`Hymn`, `Kyrie`, etc.).
  - Tapping anywhere initiates playback and expands the item.
- **Active Track Card (`.active-track-card`)**:
  - High-contrast glowing border and subtle background tint.
  - **Header Row**: Track index, title, subtitle, and live badge (`▶ PLAYING` in blue or `⏸ PAUSED` in amber).
  - **Inline Player Controls**:
    - **Touch-Friendly Scrubber**: `<input type="range" class="mobile-inline-scrubber">` bound to `audioPlayer.currentTime`.
    - **Timestamp Display**: `0:38 / 1:44`.
    - **Action Button Row**:
      - Large `[ ⏸ PAUSE TRACK / ▶ RESUME TRACK ]` primary button.
      - `[ 🔄 RESTART TRACK ]` secondary button.

### 2.4 CSS Accordion Transitions
- Uses CSS `max-height` and `opacity` transition rules to smoothly expand active track cards and collapse previous cards without abrupt scroll jumps.

---

## 3. Event Handling & State Management

1. **Real-time Scrubber Sync**: `timeupdate` event listener on `#main-audio-player` updates `#mobile-inline-scrubber` and timestamps directly without re-rendering the playlist HTML.
2. **Auto-Advance & Card Transition**: When a track finishes (`ended`), `activeTrackIndex` auto-increments, collapsing the finished track card and expanding the next track card inline.
3. **Missing Audio Handling**: Displays a `⚠️ Missing Audio` badge on missing items and disables inline expansion.

---

## 4. Verification Plan

1. **Automated Testing**: Run `pytest -v` to ensure 58 existing unit & integration tests pass cleanly.
2. **Mobile Viewport Simulation**: Verify on 375px–414px mobile browser viewports for layout integrity and touch targets.
3. **Interactive Control Verification**: Verify Play/Pause, Scrubber seeking, Track Restart, and view switching.
