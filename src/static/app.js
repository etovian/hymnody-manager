// Hymnody Manager Frontend Application Logic

let currentHymns = [];
let currentService = null;
let activeTrackIndex = -1;
let isPlaying = false;
let activeSeason = '';
let draggedHymnId = null;
let draggedItemIndex = null;
let currentRubricStatus = null;

const audioPlayer = document.getElementById('main-audio-player');

document.addEventListener('DOMContentLoaded', () => {
  fetchHymns();
  fetchOrCreateService();
  setupAudioListeners();
});

// View Switcher (Desktop vs Sanctuary Mobile Mode)
function switchView(mode) {
  const desktopView = document.getElementById('desktop-view');
  const mobileView = document.getElementById('mobile-view');
  const playerBar = document.getElementById('desktop-player-bar');
  const btnDesktop = document.getElementById('btn-desktop-view');
  const btnMobile = document.getElementById('btn-mobile-view');

  if (mode === 'desktop') {
    desktopView.classList.remove('hidden');
    mobileView.classList.add('hidden');
    playerBar.classList.remove('hidden');
    btnDesktop.classList.add('active');
    btnMobile.classList.remove('active');
  } else {
    desktopView.classList.add('hidden');
    mobileView.classList.remove('hidden');
    playerBar.classList.add('hidden');
    btnMobile.classList.add('active');
    btnDesktop.classList.remove('active');
  }
}

// Fetch Hymns Catalog
async function fetchHymns(query = '') {
  try {
    let url = `/api/hymns?q=${encodeURIComponent(query)}`;
    if (activeSeason) {
      url += `&season=${encodeURIComponent(activeSeason)}`;
    }
    const res = await fetch(url);
    currentHymns = await res.json();
    renderHymnList(currentHymns);
  } catch (err) {
    console.error("Error fetching hymns:", err);
  }
}

function handleSearch() {
  const q = document.getElementById('search-input').value;
  fetchHymns(q);
}

function filterSeason(season) {
  activeSeason = season;
  document.querySelectorAll('#season-filters .pill').forEach(btn => {
    btn.classList.toggle('active', btn.textContent === (season || 'All'));
  });
  handleSearch();
}

function renderHymnList(hymns) {
  const container = document.getElementById('hymn-list-container');
  document.getElementById('catalog-count').textContent = `${hymns.length} Tracks`;
  container.innerHTML = '';

  hymns.forEach(h => {
    const item = document.createElement('div');
    item.className = 'hymn-item';
    item.setAttribute('draggable', 'true');
    item.ondragstart = (e) => onHymnDragStart(e, h.id);

    const numTag = h.hymn_number ? `LSB ${h.hymn_number}` : `Disc ${h.disc_number}`;
    item.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="drag-handle">⋮⋮</span>
        <div>
          <span class="badge" style="margin-right: 6px;">${numTag}</span>
          <span style="font-weight: 500;">${h.title}</span>
          <div class="subtitle">Disc ${h.disc_number}, Track ${h.track_number} • ${h.liturgical_season}</div>
        </div>
      </div>
      <button class="btn btn-primary" onclick="addHymnToService(${h.id})">+ Add</button>
    `;
    container.appendChild(item);
  });
}

// Drag & Drop Handlers for Hymnal Catalog -> Service Slot
function onHymnDragStart(e, hymnId) {
  draggedHymnId = hymnId;
  draggedItemIndex = null;
  e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'catalog', hymnId }));
}

function onDragOver(e) {
  e.preventDefault();
  e.currentTarget.classList.add('drag-over');
}

function onDragLeave(e) {
  e.currentTarget.classList.remove('drag-over');
}

function onHymnDrop(e, targetIndex) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');

  if (draggedHymnId !== null) {
    // Catalog to slot drop
    assignHymnToSlot(draggedHymnId, targetIndex);
    draggedHymnId = null;
  } else if (draggedItemIndex !== null && draggedItemIndex !== targetIndex) {
    // In-list reorder drop
    reorderServiceItems(draggedItemIndex, targetIndex);
    draggedItemIndex = null;
  }
}

// In-List Item Drag Handlers
function onItemDragStart(e, itemIndex) {
  draggedItemIndex = itemIndex;
  draggedHymnId = null;
  e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'item', itemIndex }));
}

function reorderServiceItems(fromIndex, toIndex) {
  if (!currentService || !currentService.items) return;
  const items = currentService.items;
  const [movedItem] = items.splice(fromIndex, 1);
  items.splice(toIndex, 0, movedItem);

  // Update sequence order
  items.forEach((item, idx) => item.sequence_order = idx + 1);
  syncServiceItems();
}

function assignHymnToSlot(hymnId, slotIndex) {
  if (!currentService || !currentService.items || !currentService.items[slotIndex]) return;
  const hymn = currentHymns.find(h => h.id === hymnId);
  if (!hymn) return;

  const target = currentService.items[slotIndex];
  target.hymn_id = hymn.id;
  target.item_title = hymn.hymn_number ? `LSB ${hymn.hymn_number} - ${hymn.title}` : hymn.title;
  target.file_path = hymn.file_path;

  syncServiceItems();
}

// Remove Service Item
function removeServiceItem(itemIndex) {
  if (!currentService || !currentService.items) return;
  currentService.items.splice(itemIndex, 1);
  currentService.items.forEach((item, idx) => item.sequence_order = idx + 1);
  syncServiceItems();
}

// Fetch or Create Active Service
async function fetchOrCreateService() {
  try {
    const res = await fetch('/api/services');
    const services = await res.json();
    if (services.length > 0) {
      loadService(services[0].id);
    } else {
      createNewService();
    }
  } catch (err) {
    console.error("Error fetching service:", err);
  }
}

async function createNewService() {
  try {
    const res = await fetch('/api/services', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: "Sunday Worship Service",
        service_date: new Date().toISOString().split('T')[0],
        setting_preset: document.getElementById('preset-select').value || 'DS2',
        liturgical_color: "Blue"
      })
    });
    currentService = await res.json();
    renderService(currentService);
  } catch (err) {
    console.error("Error creating service:", err);
  }
}

async function loadService(serviceId) {
  try {
    const res = await fetch(`/api/services/${serviceId}`);
    currentService = await res.json();
    renderService(currentService);
  } catch (err) {
    console.error("Error loading service:", err);
  }
}

async function changeSettingPreset() {
  if (!currentService) return;
  await createNewService();
}

async function restoreOfficialPreset() {
  if (!currentService) return;
  document.getElementById('rubric-popover').classList.add('hidden');
  await createNewService();
}

function renderService(service) {
  document.getElementById('service-title-display').textContent = `Service Plan: ${service.title}`;
  document.getElementById('service-subtitle-display').textContent = `Date: ${service.service_date} | Setting: ${service.setting_preset}`;
  document.getElementById('mobile-service-title').textContent = service.title;
  document.getElementById('mobile-service-subtitle').textContent = `Setting: ${service.setting_preset}`;

  const container = document.getElementById('service-items-container');
  const mobilePlaylist = document.getElementById('mobile-playlist-container');
  container.innerHTML = '';
  mobilePlaylist.innerHTML = '';

  (service.items || []).forEach((item, index) => {
    // Desktop list item with drag handles and drop targets
    const el = document.createElement('div');
    el.className = 'service-item';
    el.setAttribute('draggable', 'true');
    el.ondragstart = (e) => onItemDragStart(e, index);
    el.ondragover = onDragOver;
    el.ondragleave = onDragLeave;
    el.ondrop = (e) => onHymnDrop(e, index);

    el.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
        <span class="drag-handle">⋮⋮</span>
        <span style="font-weight: 700; color: #64748b; width: 24px;">${String(index + 1).padStart(2, '0')}</span>
        <div>
          <span style="font-size: 11px; font-weight: 700; color: #60a5fa; text-transform: uppercase;">${item.slot_name}</span>
          <div style="font-weight: 500;">${item.item_title}</div>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <button class="btn btn-primary" onclick="playServiceTrack(${index})">▶ Play</button>
        <button class="btn-danger-text" onclick="removeServiceItem(${index})" title="Remove item">✕</button>
      </div>
    `;
    container.appendChild(el);

    // Mobile list item
    const mItem = document.createElement('div');
    mItem.className = `mobile-playlist-item ${index === activeTrackIndex ? 'active' : ''}`;
    mItem.onclick = () => playServiceTrack(index);
    mItem.innerHTML = `
      <span>${index + 1}. ${item.item_title}</span>
      <span class="subtitle">${item.hymn_id ? 'Hymn' : 'Canticle'}</span>
    `;
    mobilePlaylist.appendChild(mItem);
  });

  fetchRubricStatus(service.id);
}

function addHymnToService(hymnId) {
  if (!currentService || !currentService.items) return;
  const hymn = currentHymns.find(h => h.id === hymnId);
  if (!hymn) return;

  const targetIndex = currentService.items.findIndex(i => !i.hymn_id && i.slot_name.toLowerCase().includes('hymn'));
  if (targetIndex !== -1) {
    assignHymnToSlot(hymnId, targetIndex);
  } else {
    currentService.items.push({
      service_id: currentService.id,
      hymn_id: hymn.id,
      item_title: hymn.hymn_number ? `LSB ${hymn.hymn_number} - ${hymn.title}` : hymn.title,
      slot_name: "Selected Hymn",
      sequence_order: currentService.items.length + 1,
      file_path: hymn.file_path
    });
    syncServiceItems();
  }
}

async function syncServiceItems() {
  if (!currentService) return;
  const res = await fetch(`/api/services/${currentService.id}/items`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(currentService.items)
  });
  currentService = await res.json();
  renderService(currentService);
}

// Rubric Status Validation
async function fetchRubricStatus(serviceId) {
  try {
    const res = await fetch(`/api/services/${serviceId}/rubric`);
    currentRubricStatus = await res.json();
    updateRubricUI(currentRubricStatus);
  } catch (err) {
    console.error("Error fetching rubric status:", err);
  }
}

function updateRubricUI(status) {
  const badge = document.getElementById('rubric-badge');
  const issuesList = document.getElementById('rubric-issues-list');

  if (status.is_conformant) {
    badge.className = 'rubric-badge conformant';
    badge.textContent = `✓ Standard ${status.setting} Rubric`;
    issuesList.innerHTML = '<li>All required canticles in standard order.</li>';
  } else {
    badge.className = 'rubric-badge modified';
    badge.textContent = `⚠️ Custom Rubric (${status.issues.length} modified)`;
    issuesList.innerHTML = status.issues.map(i => `<li>${i}</li>`).join('');
  }
}

function toggleRubricPopover() {
  const popover = document.getElementById('rubric-popover');
  popover.classList.toggle('hidden');
}

// Audio Playback & Transport Controls
function playServiceTrack(index) {
  if (!currentService || !currentService.items || !currentService.items[index]) return;
  activeTrackIndex = index;
  const item = currentService.items[index];

  let audioUrl = '';
  if (item.hymn_id) {
    audioUrl = `/api/hymns/${item.hymn_id}/audio`;
  } else if (item.file_path) {
    const match = currentHymns.find(h => h.file_path === item.file_path);
    if (match) {
      audioUrl = `/api/hymns/${match.id}/audio`;
    }
  }

  if (audioUrl) {
    audioPlayer.src = audioUrl;
    audioPlayer.play();
    isPlaying = true;
    updatePlayerUI(item);
  }
}

function togglePlayPause() {
  if (!audioPlayer.src) {
    if (currentService && currentService.items.length > 0) {
      playServiceTrack(0);
    }
    return;
  }
  if (isPlaying) {
    audioPlayer.pause();
    isPlaying = false;
  } else {
    audioPlayer.play();
    isPlaying = true;
  }
  updatePlayButtonUI();
}

function playNextTrack() {
  if (!currentService || !currentService.items) return;
  if (activeTrackIndex < currentService.items.length - 1) {
    playServiceTrack(activeTrackIndex + 1);
  }
}

function playPrevTrack() {
  if (!currentService || !currentService.items) return;
  if (audioPlayer.currentTime > 3) {
    audioPlayer.currentTime = 0;
  } else if (activeTrackIndex > 0) {
    playServiceTrack(activeTrackIndex - 1);
  }
}

function updatePlayerUI(item) {
  const title = item ? item.item_title : 'No track selected';
  document.getElementById('desktop-track-title').textContent = title;
  document.getElementById('mobile-track-title').textContent = title;
  document.getElementById('mobile-track-subtitle').textContent = item ? item.slot_name : '--';
  updatePlayButtonUI();
}

function updatePlayButtonUI() {
  const dBtn = document.getElementById('desktop-play-btn');
  const mIcon = document.getElementById('mobile-play-icon');
  const mLabel = document.getElementById('mobile-play-label');

  if (isPlaying) {
    dBtn.textContent = '⏸';
    mIcon.textContent = '⏸';
    mLabel.textContent = 'PAUSE';
  } else {
    dBtn.textContent = '▶';
    mIcon.textContent = '▶';
    mLabel.textContent = 'PLAY';
  }
}

function setupAudioListeners() {
  audioPlayer.addEventListener('timeupdate', () => {
    const current = audioPlayer.currentTime || 0;
    const total = audioPlayer.duration || 0;
    const pct = total ? (current / total) * 100 : 0;

    document.getElementById('desktop-scrubber').value = pct;
    document.getElementById('mobile-progress-bar').style.width = `${pct}%`;
    document.getElementById('desktop-time-current').textContent = formatTime(current);
    document.getElementById('desktop-time-total').textContent = formatTime(total);
    document.getElementById('mobile-time-current').textContent = formatTime(current);
    document.getElementById('mobile-time-total').textContent = formatTime(total);
  });

  audioPlayer.addEventListener('ended', () => {
    playNextTrack();
  });
}

function formatTime(secs) {
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function seekAudio(pct) {
  if (audioPlayer.duration) {
    audioPlayer.currentTime = (pct / 100) * audioPlayer.duration;
  }
}

function setVolume(vol) {
  audioPlayer.volume = vol;
}

// Export Mobile Package Zip
function exportMobileZip() {
  if (!currentService) return;
  window.location.href = `/api/services/${currentService.id}/export/zip`;
}
