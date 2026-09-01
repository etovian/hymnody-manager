// Hymnody Manager Frontend Application Logic

let currentHymns = [];
let currentService = null;
let activeTrackIndex = -1;
let isPlaying = false;
let activeSeason = '';
let draggedHymnId = null;
let draggedItemIndex = null;
let activeDragMode = null; // 'insert-above', 'insert-below', or 'replace'
let currentRubricStatus = null;
let allSavedServices = [];
let explorerFilterMode = 'all';
let availableTemplates = [];
let selectedTemplateForEdit = null;

const audioPlayer = document.getElementById('main-audio-player');

document.addEventListener('DOMContentLoaded', () => {
  fetchHymns();
  loadTemplatesUI();
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
    const dateVal = document.getElementById('service-date-input').value || new Date().toISOString().split('T')[0];
    const dayVal = document.getElementById('liturgical-day-input').value || '';
    const presetVal = document.getElementById('preset-select').value || 'DS2';

    const res = await fetch('/api/services', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: "Sunday Worship Service",
        service_date: dateVal,
        liturgical_day: dayVal,
        setting_preset: presetVal,
        liturgical_color: "Green"
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

async function updateServiceMetadataFromUI() {
  if (!currentService) return;
  const dateVal = document.getElementById('service-date-input').value;
  const dayVal = document.getElementById('liturgical-day-input').value;

  try {
    const res = await fetch(`/api/services/${currentService.id}/metadata`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        service_date: dateVal,
        liturgical_day: dayVal
      })
    });
    currentService = await res.json();
    renderService(currentService);
  } catch (err) {
    console.error("Error updating service metadata:", err);
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
  const subtitle = `${service.service_date}${service.liturgical_day ? ' • ' + service.liturgical_day : ''} | Setting: ${service.setting_preset}`;
  document.getElementById('service-title-display').textContent = `Service Plan: ${service.title}`;
  document.getElementById('service-subtitle-display').textContent = subtitle;
  document.getElementById('mobile-service-title').textContent = service.title;
  document.getElementById('mobile-service-subtitle').textContent = subtitle;

  document.getElementById('service-date-input').value = service.service_date || new Date().toISOString().split('T')[0];
  document.getElementById('liturgical-day-input').value = service.liturgical_day || '';
  if (service.setting_preset) {
    document.getElementById('preset-select').value = service.setting_preset;
  }

  const container = document.getElementById('service-items-container');
  const mobilePlaylist = document.getElementById('mobile-playlist-container');
  container.innerHTML = '';
  mobilePlaylist.innerHTML = '';

  (service.items || []).forEach((item, index) => {
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
      file_path: hymn.file_path
    });
    syncServiceItems();
  }
}

async function syncServiceItems() {
  if (!currentService) return;
  currentService.items.forEach((item, idx) => item.sequence_order = idx + 1);
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
  } catch (err) {
    console.error("Error deleting service:", err);
  }
}

// Template Editor Modal Logic
async function openTemplateEditor() {
  document.getElementById('template-editor-modal').classList.remove('hidden');
  await loadTemplatesUI();
}

function closeTemplateEditor() {
  document.getElementById('template-editor-modal').classList.add('hidden');
}

async function loadTemplatesUI() {
  try {
    const res = await fetch('/api/templates');
    availableTemplates = await res.json();
    populatePresetDropdown();

    const listContainer = document.getElementById('template-list-container');
    listContainer.innerHTML = '';

    availableTemplates.forEach(t => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `template-item-btn ${selectedTemplateForEdit && selectedTemplateForEdit.id === t.id ? 'active' : ''}`;
      btn.onclick = () => selectTemplateUI(t.id);
      btn.innerHTML = `
        <span style="font-weight: 700;">${t.name}</span>
        <span class="subtitle">${t.is_builtin ? 'Built-in' : 'Custom'}</span>
      `;
      listContainer.appendChild(btn);
    });

    if (availableTemplates.length > 0 && !selectedTemplateForEdit) {
      selectTemplateUI(availableTemplates[0].id);
    }
  } catch (err) {
    console.error("Error loading templates:", err);
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

  document.querySelectorAll('.template-item-btn').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.includes(t.name));
  });

  document.getElementById('edit-template-id').value = t.id;
  document.getElementById('edit-template-name').value = t.name;
  document.getElementById('edit-template-desc').value = t.description || '';
  document.getElementById('btn-delete-template').style.display = t.is_builtin ? 'none' : 'inline-block';

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
    row.ondragover = (e) => {
      e.preventDefault();
      row.classList.add('drag-over');
    };
    row.ondragleave = () => {
      row.classList.remove('drag-over');
    };
    row.ondrop = (e) => {
      e.preventDefault();
      row.classList.remove('drag-over');
      onTemplateSlotDrop(e, idx);
    };

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
      <button type="button" class="btn-danger-text" onclick="removeTemplateSlotUI(${idx})" title="Delete slot">✕</button>
    `;
    container.appendChild(row);
  });
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
  if (draggedHymnId !== null && selectedTemplateForEdit) {
    const hymn = currentHymns.find(h => h.id === draggedHymnId);
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

function onTemplateSlotDrop(e, targetIdx) {
  if (!selectedTemplateForEdit || !selectedTemplateForEdit.items) return;
  
  if (draggedHymnId !== null) {
    const hymn = currentHymns.find(h => h.id === draggedHymnId);
    if (hymn) {
      selectedTemplateForEdit.items[targetIdx] = {
        slot_name: hymn.title,
        match_term: hymn.title,
        item_title: hymn.title
      };
      renderTemplateSlotsUI(selectedTemplateForEdit.items);
    }
    draggedHymnId = null;
  } else if (draggedTemplateSlotIdx !== null && draggedTemplateSlotIdx !== targetIdx) {
    const items = selectedTemplateForEdit.items;
    const [moved] = items.splice(draggedTemplateSlotIdx, 1);
    items.splice(targetIdx, 0, moved);
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
  } catch (err) {
    console.error("Error saving template:", err);
  }
}

async function deleteTemplateUI() {
  if (!selectedTemplateForEdit || !selectedTemplateForEdit.id) return;
  if (!confirm(`Are you sure you want to delete template "${selectedTemplateForEdit.name}"?`)) return;

  try {
    await fetch(`/api/templates/${selectedTemplateForEdit.id}`, { method: 'DELETE' });
    selectedTemplateForEdit = null;
    await loadTemplatesUI();
  } catch (err) {
    console.error("Error deleting template:", err);
  }
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
