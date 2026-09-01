# Missing Audio Status & Export Alerts Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Preserve 1-based item sequence numbers in exported ZIP track filenames/playlists when items are missing audio, and add visual status indicators, play button tooltips, and pre-export confirmation alerts in the frontend UI.

**Architecture:** Update `export_service_zip` in `src/exporter.py` to use `sequence_order` for track naming (`01`, `03`, `05`). Add CSS styles and JS logic in `src/static/app.js` to highlight missing audio items, disable unplayable tracks, and prompt confirmation before exporting zip packages with missing files.

**Tech Stack:** Python 3.11, FastAPI, pytest, Vanilla JavaScript (ES6), HTML5/CSS3.

---

### Task 1: Preserve Track Numbering in Exporter

**Files:**
- Modify: `src/exporter.py`
- Test: `tests/test_exporter.py`

**Step 1: Write the failing test**

Add `test_export_service_zip_preserves_track_numbering_for_missing_files` to `tests/test_exporter.py`:

```python
def test_export_service_zip_preserves_track_numbering_for_missing_files(tmp_path):
    db_path = str(tmp_path / "test_export_seq.db")
    init_db(db_path)
    
    # Create sample hymn for item 1 and item 3
    sample_hymn = tmp_path / "1-01 331 - Test Hymn.m4a"
    sample_hymn.write_bytes(b"dummy m4a content")
    
    hymns = [
        {'id': 1, 'hymn_number': 331, 'title': 'Test Hymn 1', 'disc_number': 1, 'track_number': 1, 'file_path': str(sample_hymn), 'liturgical_season': 'General'},
        {'id': 2, 'hymn_number': 332, 'title': 'Test Hymn 3', 'disc_number': 1, 'track_number': 2, 'file_path': str(sample_hymn), 'liturgical_season': 'General'}
    ]
    save_hymns(hymns, db_path=db_path)
    
    items = [
        {'hymn_id': 1, 'slot_name': 'Opening Hymn', 'item_title': 'Test Hymn 1', 'sequence_order': 1, 'file_path': str(sample_hymn)},
        {'hymn_id': None, 'slot_name': 'Venite', 'item_title': 'Venite (O Come)', 'sequence_order': 2, 'file_path': ''},
        {'hymn_id': 2, 'slot_name': 'Office Hymn', 'item_title': 'Test Hymn 3', 'sequence_order': 3, 'file_path': str(sample_hymn)}
    ]
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (service_date, title, setting_preset) VALUES ('2026-09-01', 'Test Matins', 'Matins')")
        s_id = cursor.lastrowid
        for it in items:
            cursor.execute("""
                INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (s_id, it['hymn_id'], it['item_title'], it['slot_name'], it['sequence_order'], it['file_path']))
        conn.commit()
        
    zip_bytes = export_service_zip(s_id, db_path=db_path)
    assert zip_bytes is not None
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        namelist = zf.namelist()
        assert "01_Opening_Hymn_Test_Hymn_1.m4a" in namelist
        assert "03_Office_Hymn_Test_Hymn_3.m4a" in namelist
        assert "02_Venite_Venite_(O_Come).m4a" not in namelist
        
        m3u_content = zf.read("playlist.m3u").decode('utf-8')
        assert "01_Opening_Hymn_Test_Hymn_1.m4a" in m3u_content
        assert "03_Office_Hymn_Test_Hymn_3.m4a" in m3u_content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_exporter.py -v`

**Step 3: Write minimal implementation**

In `src/exporter.py`:

```python
def export_service_zip(service_id, db_path="hymnody.db"):
    service = get_service_details(service_id, db_path=db_path)
    if not service:
        return None
        
    buf = io.BytesIO()
    m3u_lines = ["#EXTM3U\n"]
    
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(service.get('items', []), start=1):
            file_path = item.get('file_path')
            raw_title = item.get('item_title', f"Track_{idx}")
            slot = item.get('slot_name', f"Slot_{idx}")
            seq_num = item.get('sequence_order', idx)
            
            clean_title = re.sub(r'[\/:*?"<>|]', '_', f"{slot}_{raw_title}").replace(' ', '_')
            filename = f"{seq_num:02d}_{clean_title}.m4a"
            
            if file_path and os.path.exists(file_path):
                zf.write(file_path, arcname=filename)
                m3u_lines.append(f"#EXTINF:-1,{raw_title}\n{filename}\n")
                
        zf.writestr("playlist.m3u", "".join(m3u_lines))
        
    return buf.getvalue()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_exporter.py -v`

**Step 5: Commit**

Command:
`python -c "import subprocess; subprocess.run(['git', 'add', 'src/exporter.py', 'tests/test_exporter.py'], check=True); subprocess.run(['git', 'commit', '-m', 'feat: preserve sequence numbering for exported track zip files and playlists'], check=True)"`

---

### Task 2: Frontend Visual Badges & Play Control State

**Files:**
- Modify: `src/static/styles.css`
- Modify: `src/static/app.js:464-520,1008-1030`

**Step 1: Add CSS badge & button disabled styles**

In `src/static/styles.css`, add styles for `.badge-missing-audio` and `.btn-disabled-audio`:

```css
.badge-missing-audio {
  background-color: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.4);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}
.btn-disabled-audio {
  background-color: #334155 !important;
  color: #94a3b8 !important;
  cursor: not-allowed !important;
  opacity: 0.7;
}
```

**Step 2: Update item card rendering in `src/static/app.js`**

Update `renderService(service)` to inspect `item.file_path` and render badge & transport state:
- If `!item.file_path || !item.file_path.trim()`, show `<span class="badge-missing-audio">⚠️ Missing Audio</span>` and `<button class="btn btn-disabled-audio" onclick="playServiceTrack(${index})" title="No audio file bound to this item">⚠️ No Audio</button>`.
- In `playServiceTrack(index)`, if `!item.file_path`, display notification: `alert("No audio file bound to this item. You can drag a track from the hymnal catalog to bind audio.")`.

**Step 3: Run existing automated tests**

Run: `pytest -v`

**Step 4: Commit**

Command:
`python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/styles.css', 'src/static/app.js'], check=True); subprocess.run(['git', 'commit', '-m', 'feat: add visual missing audio badges and transport control states'], check=True)"`

---

### Task 3: Pre-Export Warning Confirmation Dialog

**Files:**
- Modify: `src/static/app.js:1124-1135`

**Step 1: Implement export pre-check alert**

In `exportMobileZip()` in `src/static/app.js`:

```javascript
async function exportMobileZip() {
  if (!currentService) return;
  if (!currentService.id || isServiceDirty) {
    await saveActiveServiceUI();
  }
  if (!currentService || !currentService.id) {
    alert("Please save the service plan before exporting.");
    return;
  }

  const missingItems = (currentService.items || []).filter(item => !item.file_path || !item.file_path.trim());
  if (missingItems.length > 0) {
    const listStr = missingItems.map(it => `• Item ${String(it.sequence_order).padStart(2, '0')}: ${it.slot_name} (${it.item_title})`).join('\n');
    const msg = `Notice: ${missingItems.length} item(s) in this worship service plan do not have audio files bound:\n\n${listStr}\n\nThese items will be omitted from the exported ZIP package. Track sequence numbering will be preserved for exported files.\n\nDo you want to proceed with export anyway?`;
    if (!confirm(msg)) {
      return;
    }
  }

  window.location.href = `/api/services/${currentService.id}/export/zip`;
}
```

**Step 2: Run test suite to verify full integration**

Run: `pytest -v`

**Step 3: Commit**

Command:
`python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js'], check=True); subprocess.run(['git', 'commit', '-m', 'feat: add pre-export confirmation dialog for missing audio tracks'], check=True)"`
