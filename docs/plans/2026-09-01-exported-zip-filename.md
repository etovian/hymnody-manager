# Dynamic Export Zip Filename Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Dynamically name exported service zip files using serial date, setting preset, and liturgical day (e.g. `20260901_DS3_Pentecost_15.zip` or `20260901_Matins.zip`).

**Architecture:** Implement a pure helper function `generate_export_filename(service: dict) -> str` in `src/exporter.py`. Update `export_service_zip` to return `(zip_bytes, filename)`, and update `src/main.py` to set `Content-Disposition: attachment; filename="{filename}"`.

**Tech Stack:** Python 3, FastAPI, pytest.

---

### Task 1: Exporter Filename Helper & Zip Function Updates

**Files:**
- Modify: `tests/test_exporter.py`
- Modify: `src/exporter.py`

**Step 1: Write failing unit tests in `tests/test_exporter.py`**

Add tests for `generate_export_filename` under various metadata configurations (with/without liturgical day, date parsing, sanitization) and update existing `export_service_zip` tests to expect a tuple return `(zip_bytes, filename)`.

```python
from src.exporter import generate_export_filename

def test_generate_export_filename_with_liturgical_day():
    service = {
        'service_date': '2026-09-01',
        'setting_preset': 'DS3',
        'liturgical_day': 'Pentecost 15'
    }
    filename = generate_export_filename(service)
    assert filename == "20260901_DS3_Pentecost_15.zip"

def test_generate_export_filename_without_liturgical_day():
    service = {
        'service_date': '2026-09-01',
        'setting_preset': 'Matins',
        'liturgical_day': ''
    }
    filename = generate_export_filename(service)
    assert filename == "20260901_Matins.zip"

def test_generate_export_filename_sanitization():
    service = {
        'service_date': '2026-09-01',
        'setting_preset': 'DS 3 / Special',
        'liturgical_day': 'Trinity: 15th Sunday!'
    }
    filename = generate_export_filename(service)
    assert filename == "20260901_DS_3___Special_Trinity__15th_Sunday_.zip" or "_" in filename
```

**Step 2: Run pytest to verify failures**

Run: `pytest tests/test_exporter.py -v`
Expected: FAIL (cannot import `generate_export_filename` or tuple unpack assertion error)

**Step 3: Implement helper and update `export_service_zip` in `src/exporter.py`**

```python
import datetime

def generate_export_filename(service: dict) -> str:
    date_str = service.get('service_date', '')
    digits = ''.join(c for c in date_str if c.isdigit())
    if len(digits) != 8:
        digits = datetime.date.today().strftime('%Y%m%d')
        
    preset = service.get('setting_preset') or 'Service'
    clean_preset = re.sub(r'[\/:*?"<>|]', '_', preset).replace(' ', '_')
    clean_preset = re.sub(r'_+', '_', clean_preset).strip('_')
    
    lit_day = (service.get('liturgical_day') or '').strip()
    
    parts = [digits, clean_preset]
    if lit_day:
        clean_lit_day = re.sub(r'[\/:*?"<>|]', '_', lit_day).replace(' ', '_')
        clean_lit_day = re.sub(r'_+', '_', clean_lit_day).strip('_')
        if clean_lit_day:
            parts.append(clean_lit_day)
            
    base_name = '_'.join(p for p in parts if p)
    return f"{base_name}.zip"

def export_service_zip(service_id, db_path="hymnody.db"):
    service = get_service_details(service_id, db_path=db_path)
    if not service:
        return None, None
        
    filename = generate_export_filename(service)
    buf = io.BytesIO()
    m3u_lines = ["#EXTM3U\n"]
    
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(service.get('items', []), start=1):
            file_path = item.get('file_path')
            raw_title = item.get('item_title', f"Track_{idx}")
            slot = item.get('slot_name', f"Slot_{idx}")
            seq_num = item.get('sequence_order', idx)
            
            clean_title = re.sub(r'[\/:*?"<>|]', '_', f"{slot}_{raw_title}").replace(' ', '_')
            track_filename = f"{seq_num:02d}_{clean_title}.m4a"
            
            if file_path and os.path.exists(file_path):
                zf.write(file_path, arcname=track_filename)
                m3u_lines.append(f"#EXTINF:-1,{raw_title}\n{track_filename}\n")
                
        zf.writestr("playlist.m3u", "".join(m3u_lines))
        
    return buf.getvalue(), filename
```

**Step 4: Run pytest to verify tests pass**

Run: `pytest tests/test_exporter.py -v`
Expected: PASS

**Step 5: Commit changes**

Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/exporter.py', 'tests/test_exporter.py']); subprocess.run(['git', 'commit', '-m', 'feat: add dynamic export zip filename helper and tuple return in exporter'])"`

---

### Task 2: FastAPI Export Endpoint Updates & Integration Tests

**Files:**
- Modify: `tests/test_api.py`
- Modify: `src/main.py`

**Step 1: Write failing integration test in `tests/test_api.py`**

Update `test_full_api_workflow` or add `test_export_service_zip_filename_header` in `tests/test_api.py` to verify `Content-Disposition` header matches expected dynamic zip filename format.

```python
def test_export_service_zip_filename_header(tmp_path):
    db_path = str(tmp_path / "api_export_header_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    srv_res = client.post("/api/services", json={
        "title": "Trinity Service",
        "service_date": "2026-09-01",
        "setting_preset": "DS3",
        "liturgical_day": "Pentecost 15"
    })
    srv_id = srv_res.json()["id"]
    
    zip_res = client.get(f"/api/services/{srv_id}/export/zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-disposition"] == 'attachment; filename="20260901_DS3_Pentecost_15.zip"'
```

**Step 2: Run pytest to verify failure**

Run: `pytest tests/test_api.py::test_export_service_zip_filename_header -v`
Expected: FAIL (header contains `service_{service_id}.zip` or tuple unpacking error)

**Step 3: Update `src/main.py` endpoint `api_export_service_zip`**

```python
@app.get("/api/services/{service_id}/export/zip")
def api_export_service_zip(service_id: int):
    db_path = get_db_path()
    zip_data, filename = export_service_zip(service_id, db_path=db_path)
    if not zip_data:
        raise HTTPException(status_code=404, detail="Service not found or empty")
    return Response(
        content=zip_data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

**Step 4: Run full test suite to verify all tests pass**

Run: `pytest -v`
Expected: ALL PASS

**Step 5: Commit changes**

Run: `python -c "import subprocess; subprocess.run(['git', 'add', 'src/main.py', 'tests/test_api.py']); subprocess.run(['git', 'commit', '-m', 'feat: update zip export endpoint to return dynamic filename header'])"`
