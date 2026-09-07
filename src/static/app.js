// Hymnody Manager Frontend Application Logic

let currentHymns = [];
let currentService = null;
let mobileService = null;
let activeTrackIndex = -1;
let isPlaying = false;
let currentView = 'desktop';
let activeSeason = '';
let draggedHymnId = null;
let draggedItemIndex = null;
let activeDragMode = null; // 'insert-above', 'insert-below', or 'replace'
let currentRubricStatus = null;
let allSavedServices = [];
let explorerFilterMode = 'all';
let availableTemplates = [];
let selectedTemplateForEdit = null;
let activeCatalogTab = 'hymn';
const HYMN_SEASONS = [
  { label: 'All Hymns', value: '' },
  { label: 'Advent', value: 'Advent' },
  { label: 'Baptism', value: 'Baptism' },
  { label: 'Christmas', value: 'Christmas' },
  { label: 'Communion', value: 'Communion' },
  { label: 'Confession', value: 'Confession' },
  { label: 'Easter', value: 'Easter' },
  { label: 'Epiphany', value: 'Epiphany' },
  { label: 'General', value: 'General' },
  { label: 'Lent', value: 'Lent' },
  { label: 'Pentecost', value: 'Pentecost' },
  { label: 'Praise', value: 'Praise' },
  { label: 'Trust & Comfort', value: 'Trust & Comfort' }
];

const LITURGY_SERVICES = [
  { label: 'All Services', value: '' },
  { label: 'Compline', value: 'Compline' },
  { label: 'DS1', value: 'DS1' },
  { label: 'DS2', value: 'DS2' },
  { label: 'DS3', value: 'DS3' },
  { label: 'DS4', value: 'DS4' },
  { label: 'DS5', value: 'DS5' },
  { label: 'Evening Prayer', value: 'Evening Prayer' },
  { label: 'Matins', value: 'Matins' },
  { label: 'Morning Prayer', value: 'Morning Prayer' },
  { label: 'Psalm Tones', value: 'Psalm Tones' },
  { label: 'Vespers', value: 'Vespers' }
];

const audioPlayer = document.getElementById('main-audio-player');

document.addEventListener('DOMContentLoaded', () => {
  renderFilterDropdown();
  fetchHymns();
  loadTemplatesUI();
  fetchOrCreateService();
  setupAudioListeners();
});

// View Switcher (Desktop vs Sanctuary Mobile Mode)
function switchView(mode) {
  currentView = mode;
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
    let url = `/api/hymns?q=${encodeURIComponent(query)}&category_type=${activeCatalogTab}`;
    if (activeSeason) {
      url += `&season=${encodeURIComponent(activeSeason)}`;
    }
    const res = await fetch(url);
    currentHymns = await res.json();
    renderHymnList(currentHymns);
    searchModalCatalog();
  } catch (err) {
    console.error("Error fetching hymns:", err);
    showToast(err.message || "Network error", "error", "API Error");
  }
}

function switchCatalogTab(tab) {
  activeCatalogTab = tab;
  activeSeason = '';
  const tabHymns = document.getElementById('tab-hymns');
  const tabLiturgy = document.getElementById('tab-liturgy');
  if (tabHymns) tabHymns.classList.toggle('active', tab === 'hymn');
  if (tabLiturgy) tabLiturgy.classList.toggle('active', tab === 'liturgy');
  renderFilterDropdown();
  handleSearch();
}

function renderFilterDropdown() {
  const select = document.getElementById('season-select');
  if (!select) return;
  select.innerHTML = '';
  const list = activeCatalogTab === 'hymn' ? HYMN_SEASONS : LITURGY_SERVICES;
  list.forEach(opt => {
    const el = document.createElement('option');
    el.value = opt.value;
    el.textContent = opt.label;
    el.selected = (activeSeason === opt.value);
    select.appendChild(el);
  });
}

function handleSearch() {
  const q = document.getElementById('search-input').value;
  fetchHymns(q);
}

function filterSeason(val) {
  activeSeason = val;
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
      <button class="btn btn-primary" onclick="playCatalogHymn(${h.id})">▶ Play</button>
    `;
    container.appendChild(item);
  });
}

function playCatalogHymn(hymnId) {
  const hymn = currentHymns.find(h => h.id === hymnId);
  if (!hymn) return;
  activeTrackIndex = -1;
  const audioUrl = `/api/hymns/${hymnId}/audio`;
  audioPlayer.src = audioUrl;
  audioPlayer.play();
  isPlaying = true;
  const itemTitle = hymn.hymn_number ? `LSB ${hymn.hymn_number} - ${hymn.title}` : hymn.title;
  const slotName = hymn.liturgical_season ? `Hymnal Catalog • ${hymn.liturgical_season}` : `Hymnal Catalog`;
  updatePlayerUI({ item_title: itemTitle, slot_name: slotName });
}

function handleCatalogAddClick(hymnId) {
  if (activePlannerTab === 'templates' && selectedTemplateForEdit) {
    const hymn = currentHymns.find(h => h.id === hymnId);
    if (hymn) {
      selectedTemplateForEdit.items = selectedTemplateForEdit.items || [];
      selectedTemplateForEdit.items.push({
        slot_name: hymn.title,
        match_term: hymn.title,
        item_title: hymn.title
      });
      renderTemplateSlotsUI(selectedTemplateForEdit.items);
    }
  } else {
    addHymnToService(hymnId);
  }
}


// Drag & Drop Handlers for Hymnal Catalog -> Service Slot
function onHymnDragStart(e, hymnId) {
  draggedHymnId = hymnId;
  draggedItemIndex = null;
  e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'catalog', hymnId }));
}

function onItemDragStart(e, itemIndex) {
  draggedItemIndex = itemIndex;
  draggedHymnId = null;
  e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'item', itemIndex }));
}

function onDragOver(e) {
  e.preventDefault();
  const rect = e.currentTarget.getBoundingClientRect();
  const y = e.clientY - rect.top;
  const pct = y / rect.height;

  e.currentTarget.classList.remove('drag-insert-above', 'drag-insert-below', 'drag-replace');

  if (pct < 0.25) {
    activeDragMode = 'insert-above';
    e.currentTarget.classList.add('drag-insert-above');
  } else if (pct > 0.75) {
    activeDragMode = 'insert-below';
    e.currentTarget.classList.add('drag-insert-below');
  } else {
    activeDragMode = 'replace';
    e.currentTarget.classList.add('drag-replace');
  }
}

function onDragLeave(e) {
  e.currentTarget.classList.remove('drag-insert-above', 'drag-insert-below', 'drag-replace');
}

function onHymnDrop(e, targetIndex) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-insert-above', 'drag-insert-below', 'drag-replace');

  const mode = activeDragMode || 'replace';
  activeDragMode = null;

  if (draggedHymnId !== null) {
    const hymn = currentHymns.find(h => h.id === draggedHymnId);
    if (!hymn || !currentService) return;
    const newTrack = {
      service_id: currentService.id,
      hymn_id: hymn.id,
      item_title: hymn.hymn_number ? `LSB ${hymn.hymn_number} - ${hymn.title}` : hymn.title,
      slot_name: "Selected Hymn",
      file_path: hymn.file_path
    };

    if (mode === 'replace') {
      assignHymnToSlot(draggedHymnId, targetIndex);
    } else if (mode === 'insert-above') {
      currentService.items.splice(targetIndex, 0, newTrack);
      syncServiceItems();
    } else if (mode === 'insert-below') {
      currentService.items.splice(targetIndex + 1, 0, newTrack);
      syncServiceItems();
    }
    draggedHymnId = null;
  } else if (draggedItemIndex !== null) {
    if (draggedItemIndex === targetIndex && mode === 'replace') return;
    const items = currentService.items;
    const [movedItem] = items.splice(draggedItemIndex, 1);
    
    let destIndex = targetIndex;
    if (mode === 'insert-below') {
      destIndex = targetIndex + (draggedItemIndex < targetIndex ? 0 : 1);
    } else if (mode === 'insert-above') {
      destIndex = targetIndex - (draggedItemIndex < targetIndex ? 1 : 0);
      if (destIndex < 0) destIndex = 0;
    }
    
    items.splice(destIndex, 0, movedItem);
    syncServiceItems();
    draggedItemIndex = null;
  }
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

function removeServiceItem(itemIndex) {
  if (!currentService || !currentService.items) return;
  currentService.items.splice(itemIndex, 1);
  syncServiceItems();
}

let isServiceDirty = false;

function markServiceDirty() {
  isServiceDirty = true;
  const saveBtn = document.getElementById('btn-save-service');
  if (saveBtn) {
    saveBtn.textContent = '💾 Save Service *';
    saveBtn.classList.remove('btn-emerald');
    saveBtn.classList.add('btn-primary');
    saveBtn.style.border = '2px solid #3b82f6';
  }
}

function markServiceClean() {
  isServiceDirty = false;
  const saveBtn = document.getElementById('btn-save-service');
  if (saveBtn) {
    saveBtn.textContent = '💾 Save Service';
    saveBtn.classList.remove('btn-primary');
    saveBtn.classList.add('btn-emerald');
    saveBtn.style.border = 'none';
  }
}

function syncServiceItems() {
  if (!currentService) return;
  (currentService.items || []).forEach((item, idx) => item.sequence_order = idx + 1);
  renderService(currentService);
  markServiceDirty();
}

function onServiceMetadataChange() {
  if (!currentService) return;
  currentService.service_date = document.getElementById('service-date-input').value;
  currentService.liturgical_day = document.getElementById('liturgical-day-input').value;
  renderService(currentService);
  markServiceDirty();
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function buildServiceOptionsHtml(services, selectedId) {
  if (!services || services.length === 0) {
    return '<option value="">No saved services found</option>';
  }
  return services.map(s => {
    const isSel = String(s.id) === String(selectedId) ? 'selected' : '';
    const title = escapeHtml(s.title || 'Service');
    const preset = s.setting_preset ? escapeHtml(` (${s.setting_preset})`) : '';
    const dateStr = s.service_date || 'No Date';
    return `<option value="${s.id}" ${isSel}>${dateStr} • ${title}${preset}</option>`;
  }).join('');
}

function selectDefaultMobileService(services) {
  if (!services || services.length === 0) return null;
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

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

function updateMobileServiceDropdown(services) {
  const mobileSelect = document.getElementById('mobile-service-select');
  if (!mobileSelect) return;
  const defService = selectDefaultMobileService(services);
  const selectedId = defService ? defService.id : null;
  mobileSelect.innerHTML = buildServiceOptionsHtml(services, selectedId);
  if (selectedId && (!mobileService || mobileService.id !== selectedId)) {
    onMobileServiceSelectChanged(selectedId);
  }
}

// Fetch or Create Active Service
async function fetchOrCreateService() {
  try {
    const res = await fetch('/api/services');
    const services = await res.json();
    allSavedServices = services;
    updateMobileServiceDropdown(services);
    if (services.length > 0) {
      await loadService(services[0].id);
    } else {
      await createDraftServiceLocally();
    }
  } catch (err) {
    console.error("Error fetching service:", err);
    showToast(err.message || "Network error", "error", "API Error");
    await createDraftServiceLocally();
  }
}

async function createDraftServiceLocally(presetVal = 'DS2') {
  const dateVal = document.getElementById('service-date-input')?.value || new Date().toISOString().split('T')[0];
  const dayVal = document.getElementById('liturgical-day-input')?.value || '';

  let allTracks = currentHymns;
  try {
    const res = await fetch('/api/hymns');
    allTracks = await res.json();
  } catch (err) {
    console.error("Error fetching all tracks for template matching:", err);
  }

  let rawItems = [];
  const tmpl = availableTemplates.find(t => t.name === presetVal);
  if (tmpl && tmpl.items && tmpl.items.length > 0) {
    rawItems = tmpl.items;
  } else {
    rawItems = [
      { slot_name: "Opening Hymn", item_title: "Invocation / Opening Hymn", match_term: "HYMN_SLOT" },
      { slot_name: "Kyrie", item_title: "Kyrie", match_term: `${presetVal} - Kyrie` },
      { slot_name: "Gloria", item_title: "Gloria in Excelsis", match_term: `${presetVal} - Gloria in Excelsis` },
      { slot_name: "Salutation", item_title: "Salutation", match_term: `${presetVal} - Salutation` },
      { slot_name: "Collect", item_title: "Collect of the Day", match_term: `${presetVal} - Collect of the Day` },
      { slot_name: "Hymn of the Day", item_title: "Hymn of the Day", match_term: "HYMN_SLOT" },
      { slot_name: "Offertory", item_title: "Offertory", match_term: `${presetVal} - Offertory` },
      { slot_name: "Sanctus", item_title: "Sanctus", match_term: `${presetVal} - Sanctus` },
      { slot_name: "Agnus Dei", item_title: "Agnus Dei", match_term: `${presetVal} - Agnus Dei` },
      { slot_name: "Distribution 1", item_title: "Distribution Hymn 1", match_term: "HYMN_SLOT" },
      { slot_name: "Distribution 2", item_title: "Distribution Hymn 2", match_term: "HYMN_SLOT" },
      { slot_name: "Nunc Dimittis", item_title: "Nunc Dimittis", match_term: `${presetVal} - Nunc Dimittis` },
      { slot_name: "Closing Hymn", item_title: "Closing Hymn", match_term: "HYMN_SLOT" }
    ];
  }

  const tmplItems = rawItems.map((it, idx) => {
    const isHymnSlot = !it.match_term || it.match_term === 'HYMN_SLOT';
    let hymnId = null;
    let filePath = "";
    let itemTitle = it.item_title || it.slot_name;

    if (!isHymnSlot) {
      const termLower = (it.match_term || '').toLowerCase();
      const exactMatch = allTracks.find(h => (h.title || '').toLowerCase() === termLower);
      const prefixMatch = exactMatch || allTracks.find(h => (h.title || '').toLowerCase().startsWith(termLower));
      const match = prefixMatch || allTracks.find(h => {
        const titleLower = (h.title || '').toLowerCase();
        return titleLower.includes(termLower) || termLower.includes(titleLower);
      });
      if (match) {
        hymnId = match.id;
        filePath = match.file_path;
        itemTitle = match.title;
      }
    }

    return {
      slot_name: it.slot_name,
      item_title: itemTitle,
      match_term: it.match_term,
      hymn_id: hymnId,
      sequence_order: idx + 1,
      file_path: filePath
    };
  });

  currentService = {
    id: null,
    title: "Sunday Worship Service",
    service_date: dateVal,
    liturgical_day: dayVal,
    setting_preset: presetVal,
    liturgical_color: "Green",
    items: tmplItems
  };

  renderService(currentService);
  markServiceDirty();
}

async function createNewService() {
  const presetVal = document.getElementById('preset-select')?.value || 'DS2';
  await createDraftServiceLocally(presetVal);
  showToast("Created new service plan", "info", "New Service");
}

async function changeSettingPreset() {
  const select = document.getElementById('preset-select');
  const presetVal = select ? select.value : 'DS2';
  const presetKey = presetVal;
  await createDraftServiceLocally(presetVal);
  showToast(`Switched setting preset to ${presetKey}`, "info");
}

async function restoreOfficialPreset() {
  try {
    document.getElementById('rubric-popover').classList.add('hidden');
    const presetVal = currentService?.setting_preset || 'DS2';
    await createDraftServiceLocally(presetVal);
  } catch (err) {
    console.error("Error restoring official preset:", err);
    showToast(err.message || "Network error", "error", "API Error");
  }
}

async function loadService(serviceId) {
  try {
    const res = await fetch(`/api/services/${serviceId}`);
    currentService = await res.json();
    renderService(currentService);
    markServiceClean();
  } catch (err) {
    console.error("Error loading service:", err);
  }
}

async function saveActiveServiceUI() {
  if (!currentService) return;

  const dateVal = document.getElementById('service-date-input').value || new Date().toISOString().split('T')[0];
  const dayVal = document.getElementById('liturgical-day-input').value || '';
  const presetVal = document.getElementById('preset-select').value || 'DS2';

  currentService.service_date = dateVal;
  currentService.liturgical_day = dayVal;
  currentService.setting_preset = presetVal;

  try {
    if (!currentService.id) {
      const res = await fetch('/api/services', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: currentService.title || "Sunday Worship Service",
          service_date: currentService.service_date,
          liturgical_day: currentService.liturgical_day,
          setting_preset: currentService.setting_preset,
          liturgical_color: currentService.liturgical_color || "Green"
        })
      });
      const created = await res.json();
      currentService.id = created.id;

      (currentService.items || []).forEach(it => it.service_id = created.id);
      const itemsRes = await fetch(`/api/services/${created.id}/items`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentService.items)
      });
      currentService = await itemsRes.json();
    } else {
      await fetch(`/api/services/${currentService.id}/metadata`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_date: currentService.service_date,
          liturgical_day: currentService.liturgical_day,
          title: currentService.title
        })
      });

      const itemsRes = await fetch(`/api/services/${currentService.id}/items`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentService.items)
      });
      currentService = await itemsRes.json();
    }

    renderService(currentService);
    markServiceClean();

    const saveBtn = document.getElementById('btn-save-service');
    if (saveBtn) {
      saveBtn.textContent = '✓ Saved!';
      setTimeout(() => { markServiceClean(); }, 1500);
    }
    showToast("Service plan saved successfully", "success", "Plan Saved");
  } catch (err) {
    console.error("Error saving service:", err);
    showToast(err.message || "Failed to save service plan", "error", "Save Failed");
  }
}

function renderService(service) {
  if (!service || !Array.isArray(service.items)) return;

  const subtitle = `${service.service_date || ''}${service.liturgical_day ? ' • ' + service.liturgical_day : ''} | Setting: ${service.setting_preset || ''}`;
  document.getElementById('service-title-display').textContent = `Service Plan: ${service.title || 'Sunday Service'}`;
  document.getElementById('service-subtitle-display').textContent = subtitle;

  document.getElementById('service-date-input').value = service.service_date || new Date().toISOString().split('T')[0];
  document.getElementById('liturgical-day-input').value = service.liturgical_day || '';
  if (service.setting_preset) {
    document.getElementById('preset-select').value = service.setting_preset;
  }

  const container = document.getElementById('service-items-container');
  container.innerHTML = '';

  (service.items || []).forEach((item, index) => {
    const hasAudio = Boolean(item.file_path && item.file_path.trim());
    const badgeHtml = hasAudio ? '' : '<span class="badge-missing-audio" style="margin-left: 6px;">⚠️ Missing Audio</span>';
    const playBtnHtml = hasAudio
      ? `<button class="btn btn-primary" onclick="playServiceTrack(${index})">▶ Play</button>`
      : `<button class="btn btn-disabled-audio" onclick="playServiceTrack(${index})" title="No audio file bound to this item">⚠️ No Audio</button>`;

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
          <div style="display: flex; align-items: center; gap: 4px;">
            <span style="font-size: 11px; font-weight: 700; color: #60a5fa; text-transform: uppercase;">${item.slot_name}</span>
            ${badgeHtml}
          </div>
          <div style="font-weight: 500;">${item.item_title}</div>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        ${playBtnHtml}
        <button class="btn-danger-text" onclick="removeServiceItem(${index})" title="Remove item">✕</button>
      </div>
    `;
    container.appendChild(el);
  });

  if (!mobileService) {
    mobileService = service;
    renderMobileServiceInfo();
  }
  renderMobilePlaylist();

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
      file_path: hymn.file_path
    });
    syncServiceItems();
  }
}

// Rubric Status Validation
async function fetchRubricStatus(serviceId) {
  if (!serviceId) {
    const badge = document.getElementById('rubric-badge');
    const issuesList = document.getElementById('rubric-issues-list');
    if (badge) {
      badge.className = 'rubric-badge conformant';
      badge.textContent = `✓ Standard Rubric`;
    }
    if (issuesList) {
      issuesList.innerHTML = '<li>All required canticles in standard order.</li>';
    }
    return;
  }
  try {
    const res = await fetch(`/api/services/${serviceId}/rubric`);
    if (res.ok) {
      currentRubricStatus = await res.json();
      updateRubricUI(currentRubricStatus);
    }
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

// Services Explorer Modal Logic
async function openServicesExplorer() {
  document.getElementById('services-explorer-modal').classList.remove('hidden');
  await fetchServicesExplorerList();
}

function closeServicesExplorer() {
  document.getElementById('services-explorer-modal').classList.add('hidden');
}

async function fetchServicesExplorerList() {
  try {
    const res = await fetch('/api/services');
    allSavedServices = await res.json();
    updateMobileServiceDropdown(allSavedServices);
    renderServicesExplorerList();
  } catch (err) {
    console.error("Error fetching saved services:", err);
  }
}

function setExplorerFilter(mode) {
  explorerFilterMode = mode;
  document.getElementById('explorer-filter-all').classList.toggle('active', mode === 'all');
  document.getElementById('explorer-filter-upcoming').classList.toggle('active', mode === 'upcoming');
  document.getElementById('explorer-filter-past').classList.toggle('active', mode === 'past');
  renderServicesExplorerList();
}

function renderServicesExplorerList() {
  const query = (document.getElementById('explorer-search').value || '').toLowerCase();
  const container = document.getElementById('services-explorer-list');
  container.innerHTML = '';
  const today = new Date().toISOString().split('T')[0];

  const filtered = allSavedServices.filter(s => {
    const textMatch = (s.title || '').toLowerCase().includes(query) ||
                      (s.service_date || '').toLowerCase().includes(query) ||
                      (s.liturgical_day || '').toLowerCase().includes(query);
    if (!textMatch) return false;

    if (explorerFilterMode === 'upcoming') {
      return s.service_date >= today;
    } else if (explorerFilterMode === 'past') {
      return s.service_date < today;
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div style="color: #94a3b8; font-size: 0.85rem; padding: 1rem;">No services found matching filters.</div>';
    return;
  }

  filtered.forEach(s => {
    const card = document.createElement('div');
    card.className = 'explorer-card';
    card.innerHTML = `
      <div class="flex-between">
        <span class="badge">${s.service_date}</span>
        <span class="subtitle">${s.setting_preset}</span>
      </div>
      <div style="font-weight: 700; color: white;">${s.title}</div>
      <div style="font-size: 0.75rem; color: #60a5fa;">${s.liturgical_day || 'Regular Worship Service'}</div>
      <div class="flex-between" style="margin-top: 8px;">
        <button class="btn btn-primary btn-sm" onclick="loadServiceFromExplorer(${s.id})">📂 Open</button>
        <div style="display: flex; gap: 4px;">
          <button class="btn btn-primary btn-sm" onclick="duplicateServiceFromExplorer(${s.id})" title="Duplicate">📋</button>
          <button class="btn-danger-text" onclick="deleteServiceFromExplorer(${s.id})" title="Delete">🗑️</button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

async function loadServiceFromExplorer(serviceId) {
  closeServicesExplorer();
  await loadService(serviceId);
}

async function duplicateServiceFromExplorer(serviceId) {
  try {
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const dateStr = nextWeek.toISOString().split('T')[0];

    const res = await fetch(`/api/services/${serviceId}/duplicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_date: dateStr })
    });
    const dup = await res.json();
    closeServicesExplorer();
    await loadService(dup.id);
  } catch (err) {
    console.error("Error duplicating service:", err);
  }
}

async function deleteServiceFromExplorer(serviceId) {
  if (!confirm("Are you sure you want to delete this worship service plan?")) return;
  try {
    await fetch(`/api/services/${serviceId}`, { method: 'DELETE' });
    await fetchServicesExplorerList();
    if (currentService && currentService.id === serviceId) {
      await fetchOrCreateService();
    }
    showToast("Service plan deleted", "warning", "Service Deleted");
  } catch (err) {
    console.error("Error deleting service:", err);
  }
}

// Template Editor Modal Logic
async function openTemplateEditor() {
  document.getElementById('template-editor-modal').classList.remove('hidden');
  await loadTemplatesUI();
  searchModalCatalog();
}

function closeTemplateEditor() {
  document.getElementById('template-editor-modal').classList.add('hidden');
}

function searchModalCatalog() {
  const query = (document.getElementById('modal-catalog-search')?.value || '').toLowerCase();
  const container = document.getElementById('modal-catalog-results');
  if (!container) return;
  container.innerHTML = '';

  const filtered = currentHymns.filter(h => {
    return (h.title || '').toLowerCase().includes(query) ||
           (h.hymn_number || '').toString().includes(query) ||
           (h.liturgical_season || '').toLowerCase().includes(query);
  }).slice(0, 50);

  if (filtered.length === 0) {
    container.innerHTML = '<div style="color: #94a3b8; font-size: 0.75rem; padding: 4px;">No matching audio tracks found.</div>';
    return;
  }

  filtered.forEach(h => {
    const card = document.createElement('div');
    card.style.background = '#0f172a';
    card.style.border = '1px solid #334155';
    card.style.borderRadius = '6px';
    card.style.padding = '6px 8px';
    card.style.display = 'flex';
    card.style.alignItems = 'center';
    card.style.justifyContent = 'space-between';
    card.style.cursor = 'grab';
    card.setAttribute('draggable', 'true');
    card.ondragstart = (e) => onHymnDragStart(e, h.id);

    const numTag = h.hymn_number ? `LSB ${h.hymn_number}` : `Disc ${h.disc_number}`;
    card.innerHTML = `
      <div style="overflow: hidden; flex: 1; margin-right: 6px;">
        <div style="font-size: 0.75rem; font-weight: 700; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${h.title}</div>
        <div style="font-size: 0.65rem; color: #94a3b8;">${numTag} • Track ${h.track_number}</div>
      </div>
      <button type="button" class="btn btn-primary btn-sm" style="font-size: 0.7rem; padding: 2px 6px;" onclick="playCatalogHymn(${h.id})">▶ Play</button>
    `;
    container.appendChild(card);
  });
}

let activePlannerTab = 'planner';

function switchPlannerTab(tab) {
  activePlannerTab = tab;
  const tabPlanner = document.getElementById('tab-service-planner');
  const tabTemplates = document.getElementById('tab-template-editor');
  const panelPlanner = document.getElementById('panel-service-planner');
  const panelTemplates = document.getElementById('panel-template-editor');

  if (tab === 'planner') {
    if (tabPlanner) tabPlanner.classList.add('active');
    if (tabTemplates) tabTemplates.classList.remove('active');
    if (panelPlanner) panelPlanner.classList.remove('hidden');
    if (panelTemplates) panelTemplates.classList.add('hidden');
  } else {
    if (tabTemplates) tabTemplates.classList.add('active');
    if (tabPlanner) tabPlanner.classList.remove('active');
    if (panelTemplates) panelTemplates.classList.remove('hidden');
    if (panelPlanner) panelPlanner.classList.add('hidden');

    if (!selectedTemplateForEdit && availableTemplates.length > 0) {
      selectTemplateUI(availableTemplates[0].id);
    }
  }
}

function openTemplateSelectorModal() {
  const modal = document.getElementById('template-selector-modal');
  if (modal) {
    modal.classList.remove('hidden');
    renderTemplateCardsModal();
  }
}

function closeTemplateSelectorModal() {
  const modal = document.getElementById('template-selector-modal');
  if (modal) modal.classList.add('hidden');
}

function renderTemplateCardsModal() {
  const container = document.getElementById('template-cards-container');
  if (!container) return;
  container.innerHTML = '';

  availableTemplates.forEach(t => {
    const card = document.createElement('div');
    card.className = 'template-card';
    const badgeClass = t.is_builtin ? 'badge-builtin' : 'badge-custom';
    const badgeLabel = t.is_builtin ? 'Built-in' : 'Custom';
    const slotCount = t.items ? t.items.length : 0;

    card.innerHTML = `
      <div>
        <div class="flex-between mb-1" style="align-items: flex-start; gap: 8px;">
          <h4 style="font-size: 0.95rem; font-weight: 700; color: white;">${t.name}</h4>
          <span class="${badgeClass}">${badgeLabel}</span>
        </div>
        <p class="subtitle" style="font-size: 0.75rem; margin-bottom: 6px;">${t.description || 'No description'}</p>
        <span style="font-size: 0.7rem; color: #60a5fa; font-weight: 600;">${slotCount} slots/ordinaries</span>
      </div>
      <div style="display: flex; gap: 6px; margin-top: 8px;">
        <button class="btn btn-primary btn-sm" style="flex: 1;" onclick="selectTemplateFromModal(${t.id})">Select for Editing</button>
        <button class="btn btn-emerald btn-sm" onclick="duplicateTemplateFromModal(${t.id})" title="Duplicate template">📋 Copy</button>
      </div>
    `;
    container.appendChild(card);
  });
}

function selectTemplateFromModal(templateId) {
  selectTemplateUI(templateId);
  closeTemplateSelectorModal();
}

async function duplicateTemplateFromModal(templateId) {
  const t = availableTemplates.find(item => item.id === templateId);
  if (!t) return;
  const newName = `${t.name} (Copy)`;
  const payload = {
    name: newName,
    description: t.description ? `${t.description} (Copy)` : 'Custom template copy',
    items: t.items || []
  };

  try {
    const res = await fetch('/api/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const saved = await res.json();
    await loadTemplatesUI();
    selectTemplateUI(saved.id);
    closeTemplateSelectorModal();
    showToast("Created template duplicate", "success");
  } catch (err) {
    console.error("Error duplicating template:", err);
    showToast(err.message || "Network error", "error", "API Error");
  }
}

function createNewTemplateFromModal() {
  createNewTemplateUI();
  closeTemplateSelectorModal();
  showToast("New template created", "success");
}

async function loadTemplatesUI() {
  try {
    const res = await fetch('/api/templates');
    availableTemplates = await res.json();
    availableTemplates.sort((a, b) => (a.name || '').localeCompare(b.name || '', undefined, { sensitivity: 'base' }));
    populatePresetDropdown();

    if (availableTemplates.length > 0 && !selectedTemplateForEdit) {
      selectTemplateUI(availableTemplates[0].id);
    } else if (selectedTemplateForEdit && selectedTemplateForEdit.id) {
      const updated = availableTemplates.find(item => item.id === selectedTemplateForEdit.id);
      if (updated) selectTemplateUI(updated.id);
    }
  } catch (err) {
    console.error("Error loading templates:", err);
    showToast(err.message || "Network error", "error", "API Error");
  }
}

function populatePresetDropdown() {
  const select = document.getElementById('preset-select');
  if (!select) return;
  const currentVal = select.value;
  select.innerHTML = '';
  availableTemplates.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.name;
    opt.textContent = t.name;
    select.appendChild(opt);
  });
  if (currentVal) select.value = currentVal;
}

function selectTemplateUI(templateId) {
  const t = availableTemplates.find(item => item.id === templateId);
  if (!t) return;
  selectedTemplateForEdit = t;

  const titleEl = document.getElementById('active-template-title');
  const subEl = document.getElementById('active-template-subtitle');
  if (titleEl) titleEl.textContent = t.name;
  if (subEl) subEl.textContent = `${t.is_builtin ? 'Built-in Lutheran Service Book preset' : 'Custom setting template'} • ${t.items ? t.items.length : 0} slots`;

  const editId = document.getElementById('edit-template-id');
  const editName = document.getElementById('edit-template-name');
  const editDesc = document.getElementById('edit-template-desc');
  if (editId) editId.value = t.id || '';
  if (editName) editName.value = t.name || '';
  if (editDesc) editDesc.value = t.description || '';

  const delBtn = document.getElementById('btn-delete-template');
  if (delBtn) delBtn.style.display = t.is_builtin ? 'none' : 'inline-block';

  renderTemplateSlotsUI(t.items || []);
}


let draggedTemplateSlotIdx = null;

function renderTemplateSlotsUI(items) {
  const container = document.getElementById('template-slots-editor-list');
  container.innerHTML = '';

  items.forEach((item, idx) => {
    const row = document.createElement('div');
    row.className = 'template-slot-card';
    row.setAttribute('draggable', 'true');
    
    row.ondragstart = (e) => {
      draggedTemplateSlotIdx = idx;
      draggedHymnId = null;
      e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'template-slot', idx }));
    };
    row.ondragover = onTemplateSlotDragOver;
    row.ondragleave = onTemplateSlotDragLeave;
    row.ondrop = (e) => onTemplateSlotDrop(e, idx);

    const isHymn = !item.match_term || item.match_term === 'HYMN_SLOT';
    const badgeClass = isHymn ? 'badge-hymn' : 'badge-audio';
    const badgeLabel = isHymn ? '📖 Hymn Placeholder' : `🎵 Audio: ${item.match_term}`;

    row.innerHTML = `
      <span class="drag-handle" title="Drag to reorder slot">⋮⋮</span>
      <span style="font-weight: 700; color: #64748b; width: 20px;">${String(idx + 1).padStart(2, '0')}</span>
      <div style="flex: 1; display: flex; flex-direction: column; gap: 4px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <input type="text" class="slot-name-input" value="${item.slot_name || ''}" placeholder="Slot Name (e.g. Kyrie)" style="flex: 1; background: #0f172a; color: white; border: 1px solid #334155; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;" onchange="updateTemplateItemField(${idx}, 'slot_name', this.value)">
          <span class="${badgeClass}">${badgeLabel}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <input type="text" class="match-term-input" value="${item.match_term || ''}" placeholder="Match Term (or HYMN_SLOT)" style="flex: 1; background: #0f172a; color: #94a3b8; border: 1px solid #334155; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;" onchange="updateTemplateItemField(${idx}, 'match_term', this.value)">
        </div>
      </div>
      <button type="button" class="btn btn-primary btn-sm" onclick="playTemplateSlotTrack(${idx})" title="Play slot audio" style="font-size: 0.75rem; padding: 3px 8px;">▶ Play</button>
      <button type="button" class="btn-danger-text" onclick="removeTemplateSlotUI(${idx})" title="Delete slot">✕</button>
    `;
    container.appendChild(row);
  });
}

async function playTemplateSlotTrack(slotIndex) {
  if (!selectedTemplateForEdit || !selectedTemplateForEdit.items || !selectedTemplateForEdit.items[slotIndex]) return;
  const item = selectedTemplateForEdit.items[slotIndex];
  const term = item.match_term || '';

  if (!term || term === 'HYMN_SLOT') {
    alert(`Slot "${item.slot_name}" is a generic hymn placeholder. Drag a specific track from the hymnal catalog onto this slot to bind audio.`);
    return;
  }

  // 1. Find matching track in currentHymns or via search
  let match = currentHymns.find(h => 
    h.title.toLowerCase() === term.toLowerCase() || 
    (h.hymn_number && `lsb ${h.hymn_number}`.toLowerCase() === term.toLowerCase())
  );

  if (!match) {
    try {
      const res = await fetch(`/api/hymns?q=${encodeURIComponent(term)}`);
      const results = await res.json();
      if (results && results.length > 0) {
        match = results[0];
      }
    } catch (err) {
      console.error("Error finding audio for template slot:", err);
    }
  }

  if (match) {
    activeTrackIndex = -1;
    audioPlayer.src = `/api/hymns/${match.id}/audio`;
    audioPlayer.play();
    isPlaying = true;
    const itemTitle = match.hymn_number ? `LSB ${match.hymn_number} - ${match.title}` : match.title;
    updatePlayerUI({ item_title: itemTitle, slot_name: `Template Slot • ${item.slot_name}` });
  } else {
    alert(`No audio track found matching "${term}". You can drag a track from the catalog to bind audio.`);
  }
}


function updateTemplateItemField(index, field, value) {
  if (!selectedTemplateForEdit || !selectedTemplateForEdit.items || !selectedTemplateForEdit.items[index]) return;
  selectedTemplateForEdit.items[index][field] = value;
  if (field === 'match_term') {
    renderTemplateSlotsUI(selectedTemplateForEdit.items);
  }
}

function onTemplateListDragOver(e) {
  e.preventDefault();
}

function onTemplateListDrop(e) {
  e.preventDefault();
  let hId = draggedHymnId;
  if (hId === null) {
    try {
      const data = JSON.parse(e.dataTransfer.getData('text/plain') || '{}');
      if (data.type === 'catalog') hId = data.hymnId;
    } catch (err) {}
  }

  if (hId !== null && hId !== undefined && selectedTemplateForEdit) {
    const hymn = currentHymns.find(h => h.id == hId);
    if (hymn) {
      selectedTemplateForEdit.items = selectedTemplateForEdit.items || [];
      selectedTemplateForEdit.items.push({
        slot_name: hymn.title,
        match_term: hymn.title,
        item_title: hymn.title
      });
      renderTemplateSlotsUI(selectedTemplateForEdit.items);
    }
    draggedHymnId = null;
  }
}

function onTemplateSlotDragOver(e) {
  e.preventDefault();
  const rect = e.currentTarget.getBoundingClientRect();
  const y = e.clientY - rect.top;
  const pct = y / rect.height;

  e.currentTarget.classList.remove('drag-insert-above', 'drag-insert-below', 'drag-replace', 'drag-over');

  if (pct < 0.25) {
    activeDragMode = 'insert-above';
    e.currentTarget.classList.add('drag-insert-above');
  } else if (pct > 0.75) {
    activeDragMode = 'insert-below';
    e.currentTarget.classList.add('drag-insert-below');
  } else {
    activeDragMode = 'replace';
    e.currentTarget.classList.add('drag-replace');
  }
}

function onTemplateSlotDragLeave(e) {
  if (e.relatedTarget && e.currentTarget.contains(e.relatedTarget)) return;
  e.currentTarget.classList.remove('drag-insert-above', 'drag-insert-below', 'drag-replace', 'drag-over');
}

function onTemplateSlotDrop(e, targetIdx) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove('drag-insert-above', 'drag-insert-below', 'drag-replace', 'drag-over');
  if (!selectedTemplateForEdit || !selectedTemplateForEdit.items) return;

  const mode = activeDragMode || 'replace';
  activeDragMode = null;

  let hId = draggedHymnId;
  if (hId === null) {
    try {
      const data = JSON.parse(e.dataTransfer.getData('text/plain') || '{}');
      if (data.type === 'catalog') hId = data.hymnId;
    } catch (err) {}
  }

  if (hId !== null && hId !== undefined) {
    const hymn = currentHymns.find(h => h.id == hId);
    if (hymn) {
      const newSlot = {
        slot_name: hymn.title,
        match_term: hymn.title,
        item_title: hymn.title
      };
      if (mode === 'replace') {
        selectedTemplateForEdit.items[targetIdx] = newSlot;
      } else if (mode === 'insert-above') {
        selectedTemplateForEdit.items.splice(targetIdx, 0, newSlot);
      } else if (mode === 'insert-below') {
        selectedTemplateForEdit.items.splice(targetIdx + 1, 0, newSlot);
      }
      renderTemplateSlotsUI(selectedTemplateForEdit.items);
    }
    draggedHymnId = null;
  } else if (draggedTemplateSlotIdx !== null) {
    if (draggedTemplateSlotIdx === targetIdx && mode === 'replace') return;
    const items = selectedTemplateForEdit.items;
    const [moved] = items.splice(draggedTemplateSlotIdx, 1);
    
    let destIndex = targetIdx;
    if (mode === 'insert-below') {
      destIndex = targetIdx + (draggedTemplateSlotIdx < targetIdx ? 0 : 1);
    } else if (mode === 'insert-above') {
      destIndex = targetIdx - (draggedTemplateSlotIdx < targetIdx ? 1 : 0);
      if (destIndex < 0) destIndex = 0;
    }
    
    items.splice(destIndex, 0, moved);
    renderTemplateSlotsUI(items);
    draggedTemplateSlotIdx = null;
  }
}



function addHymnPlaceholderSlotUI() {
  if (!selectedTemplateForEdit) return;
  selectedTemplateForEdit.items = selectedTemplateForEdit.items || [];
  selectedTemplateForEdit.items.push({
    slot_name: "Selected Hymn",
    match_term: "HYMN_SLOT",
    item_title: "Hymn Placeholder"
  });
  renderTemplateSlotsUI(selectedTemplateForEdit.items);
}

function addCustomSlotUI() {
  if (!selectedTemplateForEdit) return;
  selectedTemplateForEdit.items = selectedTemplateForEdit.items || [];
  selectedTemplateForEdit.items.push({
    slot_name: "New Canticle Slot",
    match_term: "DS3 - Salutation",
    item_title: "New Canticle Slot"
  });
  renderTemplateSlotsUI(selectedTemplateForEdit.items);
}

function removeTemplateSlotUI(index) {
  if (!selectedTemplateForEdit || !selectedTemplateForEdit.items) return;
  selectedTemplateForEdit.items.splice(index, 1);
  renderTemplateSlotsUI(selectedTemplateForEdit.items);
}

function createNewTemplateUI() {
  selectedTemplateForEdit = {
    id: null,
    name: "New Custom Template",
    description: "Custom worship order",
    is_builtin: 0,
    items: [
      { slot_name: "Opening Hymn", match_term: "HYMN_SLOT", item_title: "Opening Hymn" },
      { slot_name: "DS3 - Salutation", match_term: "DS3 - Salutation", item_title: "DS3 - Salutation" },
      { slot_name: "Closing Hymn", match_term: "HYMN_SLOT", item_title: "Closing Hymn" }
    ]
  };
  document.getElementById('edit-template-id').value = '';
  document.getElementById('edit-template-name').value = selectedTemplateForEdit.name;
  document.getElementById('edit-template-desc').value = selectedTemplateForEdit.description;
  document.getElementById('btn-delete-template').style.display = 'none';
  renderTemplateSlotsUI(selectedTemplateForEdit.items);
}

async function saveTemplateFromUI() {
  const idVal = document.getElementById('edit-template-id').value;
  const nameVal = document.getElementById('edit-template-name').value;
  const descVal = document.getElementById('edit-template-desc').value;

  const rows = document.querySelectorAll('#template-slots-editor-list > .template-slot-card');
  const items = [];
  rows.forEach((r, idx) => {
    const sName = r.querySelector('.slot-name-input').value;
    const mTerm = r.querySelector('.match-term-input').value;
    items.push({
      slot_name: sName,
      match_term: mTerm,
      item_title: sName,
      sequence_order: idx + 1
    });
  });

  const payload = { name: nameVal, description: descVal, items: items };
  const method = idVal ? 'PUT' : 'POST';
  const url = idVal ? `/api/templates/${idVal}` : '/api/templates';

  try {
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const saved = await res.json();
    selectedTemplateForEdit = saved;
    await loadTemplatesUI();
    showToast("Template saved successfully", "success", "Template Saved");
  } catch (err) {
    console.error("Error saving template:", err);
    showToast(err.message || "Failed to save template", "error", "Save Failed");
  }
}

async function deleteTemplateUI() {
  if (!selectedTemplateForEdit || !selectedTemplateForEdit.id) return;
  if (!confirm(`Are you sure you want to delete template "${selectedTemplateForEdit.name}"?`)) return;

  try {
    await fetch(`/api/templates/${selectedTemplateForEdit.id}`, { method: 'DELETE' });
    selectedTemplateForEdit = null;
    await loadTemplatesUI();
    showToast("Template removed", "warning", "Template Deleted");
  } catch (err) {
    console.error("Error deleting template:", err);
    showToast(err.message || "Network error", "error", "API Error");
  }
}

// Audio Playback & Transport Controls
function toggleMobileTrack(index) {
  const currentList = mobileService ? (mobileService.items || []) : [];
  if (!currentList[index]) return;
  const item = currentList[index];

  if (!item.file_path || !item.file_path.trim()) {
    showToast("No audio track bound to this item", "warning", "Missing Audio");
    return;
  }

  if (activeTrackIndex === index && isPlaying) {
    audioPlayer.pause();
    isPlaying = false;
    updatePlayButtonUI();
  } else if (activeTrackIndex === index && !isPlaying) {
    audioPlayer.play().catch(err => console.error("Playback error:", err));
    isPlaying = true;
    updatePlayButtonUI();
  } else {
    playServiceTrack(index);
  }
}

function renderMobilePlaylist() {
  const mobilePlaylist = document.getElementById('mobile-playlist-container');
  if (!mobilePlaylist) return;
  mobilePlaylist.innerHTML = '';

  const items = mobileService ? (mobileService.items || []) : [];
  if (items.length === 0) {
    mobilePlaylist.innerHTML = '<div style="color: #94a3b8; font-size: 0.9rem; padding: 1rem; text-align: center;">No service selected or service has no items.</div>';
    return;
  }

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
      badgeHtml = `<span class="subtitle" style="font-size: 0.8rem; color: #94a3b8;">${item.hymn_id ? 'Hymn' : 'Audio Track'}</span>`;
    }

    const mItem = document.createElement('div');
    mItem.className = `mobile-playlist-item ${stateClass}`;
    mItem.onclick = () => toggleMobileTrack(index);
    mItem.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: flex-start;">
        <span style="font-weight: 700; color: white;">${index + 1}. ${escapeHtml(item.item_title)}</span>
        <span class="subtitle" style="font-size: 0.8rem; color: #94a3b8;">${escapeHtml(item.slot_name)}</span>
      </div>
      <div>${badgeHtml}</div>
    `;
    mobilePlaylist.appendChild(mItem);
  });
}

async function onMobileServiceSelectChanged(serviceId) {
  if (!serviceId) return;
  try {
    const res = await fetch(`/api/services/${serviceId}`);
    if (res.ok) {
      mobileService = await res.json();
      activeTrackIndex = -1;
      isPlaying = false;
      audioPlayer.pause();
      renderMobileServiceInfo();
      renderMobilePlaylist();
    } else {
      showToast("Failed to load service", "error", "Network Error");
    }
  } catch (err) {
    console.error("Error changing mobile service:", err);
    showToast("Failed to load service", "error", "Network Error");
  }
}

function renderMobileServiceInfo() {
  if (!mobileService) return;
  const subtitle = `${mobileService.service_date || ''}${mobileService.liturgical_day ? ' • ' + mobileService.liturgical_day : ''} | Setting: ${mobileService.setting_preset || ''}`;
  const titleEl = document.getElementById('mobile-service-title');
  const subEl = document.getElementById('mobile-service-subtitle');
  if (titleEl) titleEl.textContent = mobileService.title || 'Sunday Service';
  if (subEl) subEl.textContent = subtitle;
}

function playServiceTrack(index) {
  const activeService = (currentView === 'mobile' && mobileService && mobileService.items) ? mobileService : currentService;
  if (!activeService || !activeService.items || !activeService.items[index]) return;
  activeTrackIndex = index;
  const item = activeService.items[index];

  let match = null;
  if (item.hymn_id) {
    match = currentHymns.find(h => h.id === item.hymn_id);
  }
  if (!match && item.file_path) {
    const itemPath = (item.file_path || '').replace(/\//g, '\\').toLowerCase();
    match = currentHymns.find(h => (h.file_path || '').replace(/\//g, '\\').toLowerCase() === itemPath);
  }
  if (!match && item.item_title) {
    match = currentHymns.find(h => h.title && h.title.toLowerCase() === item.item_title.toLowerCase());
  }

  let audioUrl = '';
  if (match) {
    audioUrl = `/api/hymns/${match.id}/audio`;
  } else if (item.hymn_id) {
    audioUrl = `/api/hymns/${item.hymn_id}/audio`;
  }

  if (audioUrl) {
    audioPlayer.src = audioUrl;
    audioPlayer.play().catch(err => console.error("Playback error:", err));
    isPlaying = true;
    updatePlayerUI(item);
  } else {
    showToast("No audio track bound to this item", "warning", "Missing Audio");
  }
}

function togglePlayPause() {
  const activeService = (currentView === 'mobile' && mobileService && mobileService.items) ? mobileService : currentService;
  if (!audioPlayer.src) {
    if (activeService && activeService.items && activeService.items.length > 0) {
      const nextPlayable = activeService.items.findIndex(it => Boolean(it.file_path));
      if (nextPlayable !== -1) {
        playServiceTrack(nextPlayable);
      }
    }
    return;
  }
  if (isPlaying) {
    audioPlayer.pause();
    isPlaying = false;
  } else {
    audioPlayer.play().catch(err => console.error("Playback error:", err));
    isPlaying = true;
  }
  updatePlayButtonUI();
}

function playNextTrack() {
  const activeService = (currentView === 'mobile' && mobileService && mobileService.items) ? mobileService : currentService;
  if (!activeService || !activeService.items) return;
  let nextIdx = activeTrackIndex + 1;
  while (nextIdx < activeService.items.length) {
    const item = activeService.items[nextIdx];
    if (item.hymn_id || item.file_path) {
      playServiceTrack(nextIdx);
      return;
    }
    nextIdx++;
  }
}

function playPrevTrack() {
  const activeService = (currentView === 'mobile' && mobileService && mobileService.items) ? mobileService : currentService;
  if (!activeService || !activeService.items) return;
  if (audioPlayer.currentTime > 3) {
    audioPlayer.currentTime = 0;
  } else if (activeTrackIndex > 0) {
    playServiceTrack(activeTrackIndex - 1);
  }
}

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
  const deskScrubber = document.getElementById('desktop-scrubber');
  if (deskScrubber) deskScrubber.value = 0;
  const deskCur = document.getElementById('desktop-time-current');
  if (deskCur) deskCur.textContent = formatTime(0);

  showToast("Track restarted from beginning", "info", "Track Reset");
}

function updatePlayerUI(item) {
  const title = item ? item.item_title : 'No track selected';
  document.getElementById('desktop-track-title').textContent = title;
  document.getElementById('mobile-track-title').textContent = title;
  document.getElementById('mobile-track-subtitle').textContent = item ? item.slot_name : '--';
  const restartBtn = document.getElementById('mobile-restart-btn');
  if (restartBtn) {
    restartBtn.disabled = (activeTrackIndex < 0);
  }
  updatePlayButtonUI();
}

function updatePlayButtonUI() {
  const dBtn = document.getElementById('desktop-play-btn');
  const mIcon = document.getElementById('mobile-play-icon');
  const mLabel = document.getElementById('mobile-play-label');

  if (isPlaying) {
    if (dBtn) dBtn.textContent = '⏸';
    if (mIcon) mIcon.textContent = '⏸';
    if (mLabel) mLabel.textContent = 'PAUSE';
  } else {
    if (dBtn) dBtn.textContent = '▶';
    if (mIcon) mIcon.textContent = '▶';
    if (mLabel) mLabel.textContent = 'PLAY';
  }

  renderMobilePlaylist();
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
    isPlaying = false;
    updatePlayButtonUI();
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
async function exportMobileZip() {
  try {
    if (!currentService) return;
    if (!currentService.id || isServiceDirty) {
      await saveActiveServiceUI();
    }
    if (!currentService || !currentService.id) {
      alert("Please save the service plan before exporting.");
      return;
    }

    const missingItems = (currentService.items || []).filter(item => item.is_missing || item.audio_missing || !item.file_path || !item.file_path.trim());
    if (missingItems.length > 0) {
      const listStr = missingItems.map(it => `• Item ${String(it.sequence_order || 1).padStart(2, '0')}: ${it.slot_name} (${it.item_title})`).join('\n');
      const msg = `Notice: ${missingItems.length} item(s) in this worship service plan do not have audio files bound:\n\n${listStr}\n\nThese items will be omitted from the exported ZIP package. Track sequence numbering (01, 03, 05...) will be preserved for exported files.\n\nDo you want to proceed with export anyway?`;
      if (!confirm(msg)) {
        return;
      }
    }

    showToast("Generating mobile ZIP package...", "info", "Export Started");

    const res = await fetch(`/api/services/${currentService.id}/export/zip`);
    if (!res.ok) {
      throw new Error(`Export server error (${res.status})`);
    }

    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    const contentDisposition = res.headers.get('Content-Disposition');
    let filename = `hymnody_export_${currentService.id}.zip`;
    if (contentDisposition && contentDisposition.includes('filename=')) {
      filename = contentDisposition.split('filename=')[1].replace(/["']/g, '');
    }
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);

    if (missingItems.length > 0) {
      showToast("Package downloaded with missing audio files", "warning", "Missing Audio Alert");
    } else {
      showToast("Mobile package downloaded successfully", "success", "Export Complete");
    }
  } catch (err) {
    console.error("Error exporting mobile package:", err);
    showToast(err.message || "Failed to export mobile package", "error", "Export Failed");
  }
}

// Notification Toasts Engine
function showToast(message, type = 'info', title = null, duration = null) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const iconMap = {
    success: '✓',
    info: 'ℹ',
    warning: '⚠',
    error: '✕'
  };

  const defaultDurations = {
    success: 4000,
    info: 4000,
    warning: 8000,
    error: 0
  };

  const autoDuration = duration !== null ? duration : (defaultDurations[type] ?? 4000);

  while (container.children.length >= 5) {
    container.removeChild(container.firstElementChild);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconSpan = document.createElement('span');
  iconSpan.className = 'toast-icon';
  iconSpan.textContent = iconMap[type] || 'ℹ';

  const bodyDiv = document.createElement('div');
  bodyDiv.className = 'toast-body';

  if (title) {
    const titleDiv = document.createElement('div');
    titleDiv.className = 'toast-title';
    titleDiv.textContent = title;
    bodyDiv.appendChild(titleDiv);
  }

  const msgDiv = document.createElement('div');
  msgDiv.className = 'toast-message';
  msgDiv.textContent = message;
  bodyDiv.appendChild(msgDiv);

  const closeBtn = document.createElement('button');
  closeBtn.className = 'toast-close';
  closeBtn.innerHTML = '&times;';
  closeBtn.onclick = () => removeToast(toast);

  toast.appendChild(iconSpan);
  toast.appendChild(bodyDiv);
  toast.appendChild(closeBtn);
  container.appendChild(toast);

  if (autoDuration > 0) {
    setTimeout(() => removeToast(toast), autoDuration);
  }
}

function removeToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.style.animation = 'fadeOutRight 0.2s ease-in forwards';
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 200);
}

