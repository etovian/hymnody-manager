# Sanctuary Mobile Mode Track Restart — Design Specification

**Date**: 2026-09-06  
**Status**: Validated  
**Target**: `src/static/index.html`, `src/static/app.js`, `src/static/styles.css`

---

## 1. Overview & Objectives

Sanctuary operators and church volunteers occasionally need to restart the currently active track from the beginning (e.g., if a worship service moment requires a clean re-take). This feature adds a dedicated restart control to Sanctuary Mobile Mode while guaranteeing strict playback state preservation:

1. **Dedicated Touch Target**: Add a full-width `🔄 RESTART TRACK` button in `.now-playing-box` in `#mobile-view`.
2. **Playback State Preservation**:
   - If active track is **playing**, clicking restart resets position to `0:00` and continues playing.
   - If active track is **paused**, clicking restart resets position to `0:00` and **remains paused** (`⏸ PAUSED` badge preserved) until the track card is tapped again.
3. **Disabled Guard**: Button is disabled when no track is active.

---

## 2. Component Layout & Touch Styling

### 2.1 `index.html` Changes
Added inside `.now-playing-box`:
```html
<button id="mobile-restart-btn" class="mobile-restart-btn" onclick="restartCurrentTrack()" disabled>
  <span>🔄</span> RESTART TRACK
</button>
```

### 2.2 `styles.css` Specifications
```css
.mobile-restart-btn {
  width: 100%;
  padding: 0.65rem 1rem;
  margin-top: 0.75rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: #e2e8f0;
  background-color: #334155;
  border: 1px solid #475569;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
}

.mobile-restart-btn:hover:not(:disabled) {
  background-color: #475569;
  border-color: #64748b;
}

.mobile-restart-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.mobile-restart-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## 3. JavaScript Logic (`app.js`)

```javascript
function restartCurrentTrack() {
  if (activeTrackIndex < 0 || !audioPlayer.src) {
    showToast("No active track to restart", "warning", "Restart");
    return;
  }

  // Reset playback position
  audioPlayer.currentTime = 0;

  // Immediate UI update
  const bar = document.getElementById('mobile-progress-bar');
  if (bar) bar.style.width = '0%';
  const curTime = document.getElementById('mobile-time-current');
  if (curTime) curTime.textContent = formatTime(0);

  // Preserve isPlaying status
  showToast("Track restarted from beginning", "info", "Track Reset");
}
```

In `updatePlayerUI()`:
```javascript
const restartBtn = document.getElementById('mobile-restart-btn');
if (restartBtn) {
  restartBtn.disabled = (activeTrackIndex < 0);
}
```

---

## 4. Verification & Testing Strategy

1. **Automated Unit Tests**:
   - Add test in `tests/test_e2e.py` verifying `restartCurrentTrack` behavior.
   - Run `pytest -v` across full test suite (66 passing tests).
2. **Manual Verification**:
   - Test restart while playing -> verify restarts at 0:00 and continues playing.
   - Test restart while paused -> verify resets position to 0:00 and remains paused.
