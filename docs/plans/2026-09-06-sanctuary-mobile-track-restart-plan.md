# Sanctuary Mobile Mode Track Restart Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dedicated `🔄 RESTART TRACK` button to Sanctuary Mobile Mode that resets playback to `0:00` while strictly preserving the current playback state (playing stays playing from 0:00; paused stays paused at 0:00).

**Architecture:** `<button id="mobile-restart-btn">` in `.now-playing-box` invoking `restartCurrentTrack()` in `app.js`. Handles `audioPlayer.currentTime = 0`, updates UI time/progress bar, and preserves `isPlaying` boolean state.

**Tech Stack:** Vanilla JavaScript (HTML5 Audio API), HTML5, CSS3, pytest.

---

### Task 1: Add Restart Track Button in `index.html` & CSS Styling in `styles.css`

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`

**Step 1: Modify `src/static/index.html`**
Inside `.now-playing-box` below the time-display flex container:
```html
<button id="mobile-restart-btn" class="mobile-restart-btn" onclick="restartCurrentTrack()" disabled>
  <span>🔄</span> RESTART TRACK
</button>
```

**Step 2: Add CSS rules in `src/static/styles.css`**
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

**Step 3: Run pytest**
Run `pytest -v`

**Step 4: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/styles.css']); subprocess.run(['git', 'commit', '-m', 'ui: add restart track button and CSS styles to mobile view'])"
```

---

### Task 2: Implement `restartCurrentTrack()` & Button State Management in `app.js`

**Files:**
- Modify: `src/static/app.js`

**Step 1: Add `restartCurrentTrack()` function**
```javascript
function restartCurrentTrack() {
  if (activeTrackIndex < 0 || !audioPlayer.src) {
    showToast("No active track to restart", "warning", "Restart");
    return;
  }

  audioPlayer.currentTime = 0;

  const bar = document.getElementById('mobile-progress-bar');
  if (bar) bar.style.width = '0%';
  const curTime = document.getElementById('mobile-time-current');
  if (curTime) curTime.textContent = formatTime(0);

  showToast("Track restarted from beginning", "info", "Track Reset");
}
```

**Step 2: Update `updatePlayerUI()` in `app.js`**
Enable or disable `#mobile-restart-btn` based on `activeTrackIndex >= 0`.

**Step 3: Run pytest**
Run `pytest -v`

**Step 4: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat: implement restartCurrentTrack and button enablement logic'])"
```

---

### Task 3: Add E2E Verification Test & Full Suite Run

**Files:**
- Modify: `tests/test_e2e.py`

**Step 1: Add test `test_mobile_track_restart_logic` in `tests/test_e2e.py`**
Verify `restartCurrentTrack` JS function exists and behaves properly.

**Step 2: Run full pytest test suite**
Run `pytest -v`

**Step 3: Commit**
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'test: add unit and E2E verification for track restart logic'])"
```
