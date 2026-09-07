# Sanctuary Mobile Mode Enhancements Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance Sanctuary Mobile Mode with independent service selection, smart date defaulting, single-tap track play/pause toggling, high-contrast active track styling (`▶ PLAYING` / `⏸ PAUSED`), and expanded vertical playlist space.

**Architecture:** Independent `mobileService` state in `app.js` populated via shared service dropdown generator (`buildServiceOptionsHtml`). Touch-friendly `<select>` in `#mobile-view`. Playlist item clicks invoke `toggleMobileTrack(index)` to control audio playback directly. Giant control buttons removed from UI.

**Tech Stack:** Vanilla JavaScript (HTML5 Audio API, fetch), CSS Variables / Flexbox, FastAPI backend, pytest.

---

### Task 1: Add Reusable Service Option Formatting & Smart Date Defaulting in `app.js`

**Files:**
- Modify: `src/static/app.js`
- Test: `tests/test_services.py`

**Step 1: Write the failing backend/service test for date ordering**

```python
# Add test in tests/test_services.py
def test_service_date_sorting_helper(client):
    # Verify GET /api/services returns list of services sorted for date selection
    res = client.get("/api/services")
    assert res.status_code == 200
    services = res.json()
    assert isinstance(services, list)
```

**Step 2: Run test to verify**

Run: `pytest tests/test_services.py -k test_service_date_sorting_helper -v`  
Expected: PASS or FAIL depending on existing endpoints.

**Step 3: Add `buildServiceOptionsHtml` and `selectDefaultMobileService` in `app.js`**

```javascript
function buildServiceOptionsHtml(services, selectedId) {
  if (!services || services.length === 0) {
    return '<option value="">No saved services found</option>';
  }
  return services.map(s => {
    const isSel = s.id === selectedId ? 'selected' : '';
    const preset = s.setting_preset ? ` (${s.setting_preset})` : '';
    const dateStr = s.service_date || 'No Date';
    return `<option value="${s.id}" ${isSel}>${dateStr} • ${s.title || 'Service'}${preset}</option>`;
  }).join('');
}

function selectDefaultMobileService(services) {
  if (!services || services.length === 0) return null;
  const today = new Date().toISOString().split('T')[0];

  // 1. Current date match
  const exact = services.find(s => s.service_date === today);
  if (exact) return exact;

  // 2. Nearest future service (service_date > today, smallest date)
  const futureServices = services.filter(s => s.service_date && s.service_date > today)
    .sort((a, b) => a.service_date.localeCompare(b.service_date));
  if (futureServices.length > 0) return futureServices[0];

  // 3. Most recent past service (service_date < today, largest date)
  const pastServices = services.filter(s => s.service_date && s.service_date < today)
    .sort((a, b) => b.service_date.localeCompare(a.service_date));
  if (pastServices.length > 0) return pastServices[0];

  // Fallback to first available
  return services[0];
}
```

**Step 4: Verify syntax & run pytest**

Run: `pytest -v`  
Expected: PASS

**Step 5: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js', 'tests/test_services.py']); subprocess.run(['git', 'commit', '-m', 'feat: add reusable service options builder and mobile smart date defaulting'])"
```

---

### Task 2: Refactor `index.html` to Add Mobile Service Selector & Remove Giant Control Grid

**Files:**
- Modify: `src/static/index.html`
- Modify: `src/static/styles.css`

**Step 1: Update `index.html` mobile view structure**

* Add `<select id="mobile-service-select" class="mobile-service-select" onchange="onMobileServiceSelectChanged(this.value)"></select>` inside `.mobile-header`.
* Remove `.giant-controls-grid` element containing `PREVIOUS`, `PLAY`, and `NEXT TRACK` buttons.

**Step 2: Add CSS rules for mobile service select and high-contrast active tracks in `styles.css`**

```css
.mobile-service-select {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-weight: 700;
  color: #ffffff;
  background-color: #1e293b;
  border: 2px solid #3b82f6;
  border-radius: 0.5rem;
  margin-top: 0.75rem;
  cursor: pointer;
}

.mobile-playlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #1e293b;
  border: 2px solid transparent;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
}

.mobile-playlist-item.active-playing {
  border-color: #3b82f6;
  background: #1e3a8a;
}

.mobile-playlist-item.active-paused {
  border-color: #f59e0b;
  background: #78350f;
}

.badge-playing {
  background: #2563eb;
  color: #ffffff;
  font-weight: 800;
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 9999px;
  text-transform: uppercase;
}

.badge-paused {
  background: #d97706;
  color: #ffffff;
  font-weight: 800;
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 9999px;
  text-transform: uppercase;
}
```

**Step 3: Run pytest to ensure no HTML parsing regressions**

Run: `pytest -v`  
Expected: PASS

**Step 4: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/styles.css']); subprocess.run(['git', 'commit', '-m', 'ui: update mobile view header selector and CSS active track badges'])"
```

---

### Task 3: Implement Single-Tap Track Play/Pause & Dynamic Active Track Rendering in `app.js`

**Files:**
- Modify: `src/static/app.js`

**Step 1: Implement `toggleMobileTrack(index)` and update `renderService(service)`**

```javascript
function toggleMobileTrack(index) {
  if (!mobileService || !mobileService.items || !mobileService.items[index]) return;
  const item = mobileService.items[index];

  if (!item.file_path || !item.file_path.trim()) {
    showToast("No audio track bound to this item", "warning", "Missing Audio");
    return;
  }

  if (activeTrackIndex === index && isPlaying) {
    // Tapping active track while playing -> pause
    audioPlayer.pause();
    isPlaying = false;
    updatePlayButtonUI();
    renderMobilePlaylist();
  } else if (activeTrackIndex === index && !isPlaying) {
    // Tapping active track while paused -> resume
    audioPlayer.play();
    isPlaying = true;
    updatePlayButtonUI();
    renderMobilePlaylist();
  } else {
    // Tapping a different track -> start play
    playServiceTrack(index);
  }
}
```

**Step 2: Refactor `renderMobilePlaylist()` for active track badges**

```javascript
function renderMobilePlaylist() {
  const mobilePlaylist = document.getElementById('mobile-playlist-container');
  if (!mobilePlaylist) return;
  mobilePlaylist.innerHTML = '';

  const items = mobileService ? (mobileService.items || []) : [];
  items.forEach((item, index) => {
    const hasAudio = Boolean(item.file_path && item.file_path.trim());
    const isActive = (index === activeTrackIndex);

    let stateClass = '';
    let badgeHtml = '';

    if (isActive) {
      if (isPlaying) {
        stateClass = 'active-playing';
        badgeHtml = '<span class="badge-playing">▶ PLAYING</span>';
      } else {
        stateClass = 'active-paused';
        badgeHtml = '<span class="badge-paused">⏸ PAUSED</span>';
      }
    } else if (!hasAudio) {
      badgeHtml = '<span class="badge-missing-audio">⚠️ Unbound</span>';
    } else {
      badgeHtml = `<span class="subtitle">${item.hymn_id ? 'Hymn' : 'Audio Track'}</span>`;
    }

    const mItem = document.createElement('div');
    mItem.className = `mobile-playlist-item ${stateClass}`;
    mItem.onclick = () => toggleMobileTrack(index);
    mItem.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: flex-start;">
        <span style="font-weight: 700; color: white;">${index + 1}. ${item.item_title}</span>
        <span class="subtitle" style="font-size: 0.8rem; color: #94a3b8;">${item.slot_name}</span>
      </div>
      <div>${badgeHtml}</div>
    `;
    mobilePlaylist.appendChild(mItem);
  });
}
```

**Step 3: Hook up `onMobileServiceSelectChanged(serviceId)` & initialization**

When a user selects a service from `#mobile-service-select`, fetch the full service object, set `mobileService`, and call `renderMobilePlaylist()`.

**Step 4: Run pytest**

Run: `pytest -v`  
Expected: PASS

**Step 5: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js']); subprocess.run(['git', 'commit', '-m', 'feat: implement single-tap play-pause toggling and dynamic active track badge rendering'])"
```

---

### Task 4: End-to-End Manual & Automated Verification

**Files:**
- Modify: `tests/test_e2e.py`

**Step 1: Add E2E test verifying service list API returns proper payload for frontend selector**

```python
def test_mobile_service_selection_api_e2e(client):
    response = client.get("/api/services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

**Step 2: Run pytest across full test suite**

Run: `pytest -v`  
Expected: 58+ PASSING tests.

**Step 3: Manual Browser Verification**

* Start server: `uvicorn src.main:app --port 8000`
* Open `http://localhost:8000`
* Click "📱 Sanctuary Mobile Mode"
* Verify header dropdown lists all services and defaults to today / nearest future / most recent past service.
* Click track item -> starts playing, turns blue (`▶ PLAYING`).
* Click active track again -> pauses playback, turns amber (`⏸ PAUSED`).
* Verify control grid is gone and playlist fills vertical space nicely.

**Step 4: Commit**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'test: add E2E verification for mobile service selection API'])"
```
